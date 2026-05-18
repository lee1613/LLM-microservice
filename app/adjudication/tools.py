import sqlite3
import os
from typing import Optional, Dict, Any

DB_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..',
    'data', 'health-insurance-claim', 'synthetic data', 'database.db'
)


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def get_plan_document(policy_product_code: str, claim_type: str) -> Optional[str]:
    """
    Retrieve the natural-language plan coverage document for a product+claim_type.
    This is the authoritative source for all cost-sharing parameters in Node 5.
    """
    conn = _conn()
    row = conn.execute(
        "SELECT plan_document FROM plan_documents WHERE policy_product_code = ? AND claim_type = ?",
        (policy_product_code, claim_type)
    ).fetchone()
    conn.close()
    return row['plan_document'] if row else None


def get_deductible_utilised(policy_no: str, benefit_year: int) -> float:
    """
    Sum of deductible already consumed this benefit year from deductible_ledger.
    Excludes placeholder rows where amount = 0.
    """
    conn = _conn()
    row = conn.execute(
        """SELECT COALESCE(SUM(CAST(amount AS REAL)), 0) AS total
           FROM deductible_ledger
           WHERE policy_no = ? AND benefit_year = ? AND amount > 0""",
        (policy_no, str(benefit_year))
    ).fetchone()
    conn.close()
    return float(row['total'])


def record_adjudicated_claim(
    claim_reference_draft: str,
    policy_no: str,
    claim_type: str,
    incident_date: str,
    benefit_year: int,
    net_payable: float,
    adjudication_status: str,
    adjudication_timestamp: str,
    deductible_applied: float,
) -> None:
    """
    Write net_payable to claim_utilisation and record deductible in deductible_ledger.
    Uses INSERT OR IGNORE to be idempotent on repeated test runs.
    """
    conn = _conn()
    # Write to claim_utilisation (for future annual limit checks in Node 3)
    conn.execute(
        """INSERT OR IGNORE INTO claim_utilisation
           (policy_no, claim_type, benefit_year, claim_reference_no, net_payable, status, posted_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (policy_no, claim_type, str(benefit_year), claim_reference_draft,
         net_payable, adjudication_status, adjudication_timestamp)
    )
    # Record deductible consumption
    if deductible_applied > 0:
        conn.execute(
            """INSERT OR IGNORE INTO deductible_ledger
               (policy_no, benefit_year, claim_reference_no, amount, posted_at)
               VALUES (?, ?, ?, ?, ?)""",
            (policy_no, str(benefit_year), claim_reference_draft,
             deductible_applied, adjudication_timestamp)
        )
    conn.commit()
    conn.close()
