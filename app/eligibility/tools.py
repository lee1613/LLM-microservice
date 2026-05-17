import sqlite3
import os
from typing import Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'claims.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_policy_start_date(policy_no: str) -> Optional[str]:
    """Tool: Get policy start date to calculate waiting period."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT policy_start_date
        FROM policies
        WHERE policy_no = ?
    ''', (policy_no,))
    row = cursor.fetchone()
    conn.close()
    return row['policy_start_date'] if row else None

def get_plan_benefits(policy_product_code: str, claim_type: str) -> Optional[Dict[str, Any]]:
    """Tool: Get coverage limits and waiting periods for a plan/claim type."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT covered, waiting_period_days, annual_limit, per_claim_limit,
               lifetime_limit, non_panel_reimbursement_pct
        FROM plan_benefits
        WHERE policy_product_code = ? AND claim_type = ?
    ''', (policy_product_code, claim_type))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_annual_utilised(policy_no: str, claim_type: str, benefit_year: int) -> float:
    """Tool: Get the sum of all disbursements in the current benefit year."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(SUM(net_payable), 0) AS annual_utilised
        FROM claim_utilisation
        WHERE policy_no = ?
          AND claim_type = ?
          AND benefit_year = ?
          AND status IN ('paid', 'pending')
    ''', (policy_no, claim_type, benefit_year))
    row = cursor.fetchone()
    conn.close()
    return float(row['annual_utilised'])

def get_lifetime_utilised(policy_no: str) -> float:
    """Tool: Get the sum of all disbursements for a policy over its lifetime."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(SUM(net_payable), 0) AS lifetime_utilised
        FROM claim_utilisation
        WHERE policy_no = ?
          AND status = 'paid'
    ''', (policy_no,))
    row = cursor.fetchone()
    conn.close()
    return float(row['lifetime_utilised'])
