import sqlite3
import os
from typing import Dict, Any, List, Optional
from datetime import date, datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'claims.db')

def _get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_provider(provider_registration: str) -> Optional[Dict[str, Any]]:
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT provider_name, provider_type, setting, panel_status, accreditation_expiry_date
        FROM accredited_providers
        WHERE provider_registration = ?
    ''', (provider_registration,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def is_icd10_valid(icd10_code: str) -> bool:
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM icd10_reference WHERE code = ? AND status = 'active'", (icd10_code,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def is_cpt_valid(cpt_code: str) -> bool:
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM cpt_reference WHERE code = ? AND status = 'active'", (cpt_code,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def is_cpt_icd10_plausible(icd10_code: str, cpt_code: str) -> bool:
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 1 FROM icd10_cpt_plausibility 
        WHERE icd10_code = ? AND cpt_code = ? AND plausible = 1
    ''', (icd10_code, cpt_code))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def get_triggered_exclusions(icd10_code: str, cpt_codes: List[str]) -> List[str]:
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT exclusion_key, type, value FROM exclusion_catalogue")
    exclusions = cursor.fetchall()
    conn.close()
    
    triggered = []
    for exc in exclusions:
        key = exc['exclusion_key']
        etype = exc['type']
        value = exc['value']
        
        if etype == 'icd10_prefix':
            if icd10_code.startswith(value):
                triggered.append(key)
        elif etype == 'cpt_list':
            cpt_list = [v.strip() for v in value.split(',')]
            if any(cpt in cpt_list for cpt in cpt_codes):
                triggered.append(key)
                
    return list(set(triggered))

def get_pre_auth(pre_auth_no: str) -> Optional[Dict[str, Any]]:
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT status, policy_no, authorised_amount, expiry_date
        FROM pre_authorisations
        WHERE pre_auth_no = ?
    ''', (pre_auth_no,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_physician(license_no: str) -> Optional[Dict[str, Any]]:
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT status, expiry_date, specialty
        FROM physician_registry
        WHERE physician_license_no = ?
    ''', (license_no,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def is_medically_necessary(icd10_code: str, cpt_code: str) -> bool:
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT necessity_confirmed
        FROM medical_necessity_guidelines
        WHERE icd10_code = ? AND cpt_code = ?
    ''', (icd10_code, cpt_code))
    row = cursor.fetchone()
    conn.close()
    if row and row['necessity_confirmed']:
        return True
    return False

def get_rps_benchmark(cpt_codes: List[str], provider_type: str, setting: str) -> float:
    if not cpt_codes:
        return 0.0
        
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    placeholders = ','.join('?' * len(cpt_codes))
    query = f'''
        SELECT SUM(unit_price) as rps_benchmark
        FROM rps_schedule
        WHERE cpt_code IN ({placeholders})
          AND provider_type = ?
          AND setting = ?
    '''
    params = tuple(cpt_codes) + (provider_type, setting)
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    
    return row['rps_benchmark'] if row and row['rps_benchmark'] is not None else 0.0
    
def check_substance_abuse_coverage(policy_product_code: str) -> bool:
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT substance_abuse_covered
        FROM plan_benefits
        WHERE policy_product_code = ? AND claim_type = 'hospitalisation'
    ''', (policy_product_code,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return bool(row['substance_abuse_covered'])
    return False
