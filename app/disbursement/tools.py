import sqlite3
import re
import os
from typing import Optional, Dict, Any
from datetime import date

DB_PATH       = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'health-insurance-claim', 'synthetic data', 'database.db')
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'health-insurance-claim', 'synthetic data', 'registry.db')

# Bank account number format rules per contract
BANK_FORMATS = {
    'DBS':               r'^\d{10}$',
    'POSB':              r'^\d{10}$',
    'OCBC':              r'^\d{9,10}$',
    'UOB':               r'^\d{10}$',
    'Standard Chartered':r'^\d{9}$',
}
DEFAULT_BANK_FORMAT = r'^\d{7,16}$'

# Settlement days by payment mode
SETTLEMENT_DAYS = {
    'direct_credit':   3,
    'giro':            3,
    'cheque':          7,
    'provider_direct': 5,
}


def _db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _reg():
    c = sqlite3.connect(REGISTRY_PATH)
    c.row_factory = sqlite3.Row
    return c


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Payment channel validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_bank_account(bank_name: str, bank_account_no: str) -> bool:
    pattern = BANK_FORMATS.get(bank_name, DEFAULT_BANK_FORMAT)
    return bool(re.match(pattern, bank_account_no))


def get_provider_bank_details(provider_registration: str) -> Optional[Dict[str, Any]]:
    """Look up provider bank details from accredited_providers (registry.db)."""
    conn = _reg()
    row = conn.execute(
        "SELECT provider_name, bank_name, bank_account_no, bank_branch_code FROM accredited_providers WHERE provider_registration = ?",
        (provider_registration,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Claim reference finalisation (atomic sequence increment)
# ─────────────────────────────────────────────────────────────────────────────

def finalise_claim_reference(claim_reference_draft: str, year: int) -> str:
    """
    Atomically increment claim_sequence for the given year and register the
    permanent CLM-YYYY-NNNNNNN reference in the claims table.
    Returns the new permanent reference number.
    """
    conn = _db()
    try:
        # Atomic sequence increment
        conn.execute(
            "UPDATE claim_sequence SET next_val = next_val + 1 WHERE year = ?",
            (str(year),)
        )
        row = conn.execute(
            "SELECT next_val FROM claim_sequence WHERE year = ?",
            (str(year),)
        ).fetchone()
        seq = int(row['next_val'])
        claim_ref_no = f"CLM-{year}-{seq:07d}"

        # Update the existing draft row to permanent status
        conn.execute(
            "UPDATE claims SET claim_reference_no = ?, status = 'approved' WHERE claim_reference_draft = ?",
            (claim_ref_no, claim_reference_draft)
        )
        # If no row existed (first run), insert it
        if conn.execute(
            "SELECT COUNT(*) FROM claims WHERE claim_reference_draft = ?",
            (claim_reference_draft,)
        ).fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO claims (policy_no, claim_reference_no, claim_reference_draft, claim_type, status) VALUES (?,?,?,?,?)",
                ("", claim_ref_no, claim_reference_draft, "", "approved")
            )

        conn.commit()
        return claim_ref_no
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Ledger writes
# ─────────────────────────────────────────────────────────────────────────────

def write_ledger_entries(
    policy_no: str,
    claim_type: str,
    benefit_year: int,
    claim_reference_no: str,
    net_payable: float,
    deductible_applied: float,
    posted_at: str,
) -> None:
    """
    Write the two final ledger records:
      - deductible_ledger (if deductible > 0)
      - claim_utilisation with status='paid'
    Uses INSERT OR IGNORE to be idempotent.
    """
    conn = _db()
    # deductible_ledger
    if deductible_applied > 0:
        conn.execute(
            """INSERT OR IGNORE INTO deductible_ledger
               (policy_no, benefit_year, claim_reference_no, amount, posted_at)
               VALUES (?, ?, ?, ?, ?)""",
            (policy_no, str(benefit_year), claim_reference_no, deductible_applied, posted_at)
        )
    # claim_utilisation — update to 'paid' if row already exists from adjudication
    existing = conn.execute(
        "SELECT rowid FROM claim_utilisation WHERE claim_reference_no = ?",
        (claim_reference_no,)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE claim_utilisation SET status='paid', posted_at=? WHERE claim_reference_no=?",
            (posted_at, claim_reference_no)
        )
    else:
        conn.execute(
            """INSERT OR IGNORE INTO claim_utilisation
               (policy_no, claim_type, benefit_year, claim_reference_no, net_payable, status, posted_at)
               VALUES (?, ?, ?, ?, ?, 'paid', ?)""",
            (policy_no, claim_type, str(benefit_year), claim_reference_no, net_payable, posted_at)
        )
    conn.commit()
    conn.close()
