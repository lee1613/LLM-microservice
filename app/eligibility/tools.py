import sqlite3
import os
from datetime import date
from typing import Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'health-insurance-claim', 'synthetic data', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_plan_document(policy_product_code: str, claim_type: str) -> Optional[str]:
    """Retrieve the natural-language plan coverage matrix for a given product code + claim type."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT plan_document FROM plan_documents WHERE policy_product_code = ? AND claim_type = ?",
        (policy_product_code, claim_type)
    )
    row = cursor.fetchone()
    conn.close()
    return row['plan_document'] if row else None

def get_annual_utilised(policy_no: str, claim_type: str, benefit_year: int) -> float:
    """Sum net_payable for this policy/claim_type/year with status in ('paid', 'pending')."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COALESCE(SUM(CAST(net_payable AS REAL)), 0) AS total
           FROM claim_utilisation
           WHERE policy_no = ? AND claim_type = ? AND benefit_year = ?
             AND status IN ('paid', 'pending')""",
        (policy_no, claim_type, str(benefit_year))
    )
    row = cursor.fetchone()
    conn.close()
    return float(row['total'])

def get_lifetime_utilised(policy_no: str, claim_type: str) -> float:
    """Sum net_payable for all time with status = 'paid'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COALESCE(SUM(CAST(net_payable AS REAL)), 0) AS total
           FROM claim_utilisation
           WHERE policy_no = ? AND claim_type = ? AND status = 'paid'""",
        (policy_no, claim_type)
    )
    row = cursor.fetchone()
    conn.close()
    return float(row['total'])
