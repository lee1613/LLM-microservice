import sqlite3
import os
from typing import Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'claims.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_policy_product_code(policy_no: str) -> Optional[str]:
    """Fetch the policy_product_code for a policy — fallback when Node 3 didn't propagate it."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT policy_product_code FROM policies WHERE policy_no = ?',
        (policy_no,)
    )
    row = cursor.fetchone()
    conn.close()
    return row['policy_product_code'] if row else None


def get_full_plan_benefits(policy_product_code: str, claim_type: str) -> Optional[Dict[str, Any]]:
    """
    Fetch cost-sharing parameters from plan_benefits.
    Returns: deductible_annual, co_payment_pct, co_insurance_pct,
             co_insurance_cap, non_panel_reimbursement_pct
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT deductible_annual, co_payment_pct, co_insurance_pct,
               co_insurance_cap, non_panel_reimbursement_pct
        FROM plan_benefits
        WHERE policy_product_code = ?
          AND claim_type          = ?
    ''', (policy_product_code, claim_type))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_deductible_utilised(policy_no: str, benefit_year: int) -> float:
    """
    Sum of deductible already consumed this benefit year across all claim types.
    Queries the deductible_ledger table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) AS deductible_utilised
        FROM deductible_ledger
        WHERE policy_no    = ?
          AND benefit_year = ?
    ''', (policy_no, benefit_year))
    row = cursor.fetchone()
    conn.close()
    return float(row['deductible_utilised'])


def record_adjudicated_claim(
    claim_reference_draft: str,
    policy_no: str,
    claim_type: str,
    incident_date: str,
    benefit_year: int,
    adjudication_base: float,
    deductible_applied: float,
    co_pay_amount: float,
    co_insurance_amount: float,
    net_payable: float,
    claimant_liability: float,
    adjudication_status: str,
    adjudication_timestamp: str
) -> None:
    """
    Write the adjudication result to the adjudicated_claims table and
    update the deductible_ledger if any deductible was consumed.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert into adjudicated_claims (INSERT OR REPLACE to be idempotent)
    cursor.execute('''
        INSERT OR REPLACE INTO adjudicated_claims (
            claim_reference_draft, policy_no, claim_type, incident_date,
            benefit_year, adjudication_base, deductible_applied,
            co_pay_amount, co_insurance_amount, net_payable,
            claimant_liability, adjudication_status, adjudication_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        claim_reference_draft, policy_no, claim_type, incident_date,
        benefit_year, adjudication_base, deductible_applied,
        co_pay_amount, co_insurance_amount, net_payable,
        claimant_liability, adjudication_status, adjudication_timestamp
    ))

    # Record deductible consumption in ledger if any was applied
    if deductible_applied > 0:
        cursor.execute('''
            INSERT INTO deductible_ledger (policy_no, benefit_year, claim_reference_no, amount, posted_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (policy_no, benefit_year, claim_reference_draft, deductible_applied, adjudication_timestamp))

    conn.commit()
    conn.close()
