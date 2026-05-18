import sqlite3
import os
from datetime import date
from typing import Optional, Dict, Any, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'health-insurance-claim', 'synthetic data', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_policy(policy_no: str) -> Optional[Dict[str, Any]]:
    """Tool: Query the policies table using policy_no."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT policy_holder_id, policy_status, policy_start_date, policy_expiry_date,
               policy_product_code, premium_payment_mode, next_premium_due_date
        FROM policies
        WHERE policy_no = ?
    ''', (policy_no,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_policy_member(policy_no: str, id_document_type: str, id_document_no: str) -> Optional[Dict[str, Any]]:
    """Tool: Query the policy_members table to confirm claimant identity."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT member_id, full_name, relationship, dependent_status
        FROM policy_members
        WHERE policy_no = ? AND id_document_type = ? AND id_document_no = ?
    ''', (policy_no, id_document_type, id_document_no))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_premium_arrears_count(policy_no: str, incident_date: date) -> int:
    """Tool: Check for any unpaid premium due on or before incident_date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) AS arrears_count
        FROM premium_ledger
        WHERE policy_no = ? AND due_date <= ? AND payment_status = 'unpaid'
    ''', (policy_no, str(incident_date)))
    row = cursor.fetchone()
    conn.close()
    return row['arrears_count']

def get_dependent_coverage_end_date(policy_no: str, member_id: str) -> Optional[str]:
    """Tool: Check dependent coverage end date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT dependent_coverage_end_date
        FROM policy_members
        WHERE policy_no = ? AND member_id = ?
    ''', (policy_no, member_id))
    row = cursor.fetchone()
    conn.close()
    return row['dependent_coverage_end_date'] if row else None

def get_duplicate_claims_count(policy_no: str, incident_date: date, claim_type: str) -> int:
    """Tool: Check for existing claims for the same incident."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) AS dup_count
        FROM claims
        WHERE policy_no = ? AND incident_date = ? AND claim_type = ? AND status IN ('pending', 'approved', 'paid')
    ''', (policy_no, str(incident_date), claim_type))
    row = cursor.fetchone()
    conn.close()
    return row['dup_count']
