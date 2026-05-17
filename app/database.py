import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'claims.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables for Node 2
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS policies (
            policy_no TEXT PRIMARY KEY,
            policy_holder_id TEXT,
            policy_status TEXT,
            policy_start_date TEXT,
            policy_expiry_date TEXT,
            policy_product_code TEXT,
            premium_payment_mode TEXT,
            next_premium_due_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS policy_members (
            member_id TEXT PRIMARY KEY,
            policy_no TEXT,
            full_name TEXT,
            id_document_type TEXT,
            id_document_no TEXT,
            date_of_birth TEXT,
            relationship TEXT,
            dependent_status TEXT,
            dependent_coverage_end_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS premium_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_no TEXT,
            due_date TEXT,
            payment_status TEXT,
            amount REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            claim_reference_draft TEXT PRIMARY KEY,
            claim_reference_no TEXT,
            policy_no TEXT,
            claim_type TEXT,
            incident_date TEXT,
            status TEXT,
            created_at TEXT
        )
    ''')
    
    # Create tables for Node 3
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_benefits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_product_code TEXT,
            claim_type TEXT,
            covered BOOLEAN,
            waiting_period_days INTEGER,
            annual_limit REAL,
            per_claim_limit REAL,
            lifetime_limit REAL,
            deductible_annual REAL,
            co_payment_pct REAL,
            co_insurance_pct REAL,
            co_insurance_cap REAL,
            non_panel_reimbursement_pct REAL,
            substance_abuse_covered BOOLEAN
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claim_utilisation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_no TEXT,
            claim_type TEXT,
            benefit_year INTEGER,
            claim_reference_no TEXT,
            net_payable REAL,
            status TEXT,
            posted_at TEXT
        )
    ''')
    # Create tables for Node 4
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS icd10_reference (
            code TEXT PRIMARY KEY,
            description TEXT,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cpt_reference (
            code TEXT PRIMARY KEY,
            description TEXT,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS icd10_cpt_plausibility (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icd10_code TEXT,
            cpt_code TEXT,
            plausible BOOLEAN
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medical_necessity_guidelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icd10_code TEXT,
            cpt_code TEXT,
            necessity_confirmed BOOLEAN
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rps_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpt_code TEXT,
            provider_type TEXT,
            setting TEXT,
            unit_price REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exclusion_catalogue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exclusion_key TEXT,
            type TEXT,
            value TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pre_authorisations (
            pre_auth_no TEXT PRIMARY KEY,
            policy_no TEXT,
            status TEXT,
            authorised_amount REAL,
            expiry_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accredited_providers (
            provider_registration TEXT PRIMARY KEY,
            provider_name TEXT,
            provider_type TEXT,
            setting TEXT,
            panel_status TEXT,
            accreditation_expiry_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS physician_registry (
            physician_license_no TEXT PRIMARY KEY,
            physician_name TEXT,
            specialty TEXT,
            status TEXT,
            expiry_date TEXT
        )
    ''')
    
    # Load synthetic JSON
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'health-insurance-claim', 'synthetic data')
    
    with open(os.path.join(base_dir, 'db_policies.json'), 'r') as f:
        db_policies = json.load(f)
        
    with open(os.path.join(base_dir, 'db_pre_auth_and_utilisation.json'), 'r') as f:
        db_pre_auth = json.load(f)

    with open(os.path.join(base_dir, 'db_plan_benefits.json'), 'r') as f:
        db_plan_benefits = json.load(f)
        
    with open(os.path.join(base_dir, 'db_clinical.json'), 'r') as f:
        db_clinical = json.load(f)
        
    with open(os.path.join(base_dir, 'db_providers.json'), 'r') as f:
        db_providers = json.load(f)
        
    with open(os.path.join(base_dir, 'db_physicians.json'), 'r') as f:
        db_physicians = json.load(f)

    # Insert policies
    for p in db_policies.get('policies', []):
        cursor.execute('''
            INSERT OR REPLACE INTO policies 
            (policy_no, policy_holder_id, policy_status, policy_start_date, policy_expiry_date, policy_product_code, premium_payment_mode, next_premium_due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (p['policy_no'], p['policy_holder_id'], p['policy_status'], p['policy_start_date'], p['policy_expiry_date'], p['policy_product_code'], p['premium_payment_mode'], p['next_premium_due_date']))
        
    # Insert members
    for m in db_policies.get('policy_members', []):
        cursor.execute('''
            INSERT OR REPLACE INTO policy_members
            (member_id, policy_no, full_name, id_document_type, id_document_no, date_of_birth, relationship, dependent_status, dependent_coverage_end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (m['member_id'], m['policy_no'], m['full_name'], m['id_document_type'], m['id_document_no'], m['date_of_birth'], m['relationship'], m['dependent_status'], m.get('dependent_coverage_end_date')))

    # Insert premium ledger
    for pl in db_policies.get('premium_ledger', []):
        # Prevent duplication if script is run multiple times by checking existence or just replacing
        # SQLite doesn't have INSERT OR REPLACE without unique constraints on the specific fields, 
        # so we'll just insert if it's empty or clear the table first. Let's clear ledgers and claims.
        pass

    cursor.execute('DELETE FROM premium_ledger')
    cursor.execute('DELETE FROM claims')
    cursor.execute('DELETE FROM plan_benefits')
    cursor.execute('DELETE FROM claim_utilisation')
    cursor.execute('DELETE FROM icd10_reference')
    cursor.execute('DELETE FROM cpt_reference')
    cursor.execute('DELETE FROM icd10_cpt_plausibility')
    cursor.execute('DELETE FROM medical_necessity_guidelines')
    cursor.execute('DELETE FROM rps_schedule')
    cursor.execute('DELETE FROM exclusion_catalogue')
    cursor.execute('DELETE FROM pre_authorisations')
    cursor.execute('DELETE FROM accredited_providers')
    cursor.execute('DELETE FROM physician_registry')
    
    for pl in db_policies.get('premium_ledger', []):
        cursor.execute('''
            INSERT INTO premium_ledger (policy_no, due_date, payment_status, amount)
            VALUES (?, ?, ?, ?)
        ''', (pl['policy_no'], pl['due_date'], pl['payment_status'], pl['amount']))

    # Insert claims (duplicate check scenario)
    for c in db_pre_auth.get('claims', []):
        cursor.execute('''
            INSERT INTO claims (claim_reference_draft, claim_reference_no, policy_no, claim_type, incident_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (c['claim_reference_draft'], c['claim_reference_no'], c['policy_no'], c['claim_type'], c['incident_date'], c['status'], c['created_at']))

    # Insert plan benefits
    for pb in db_plan_benefits.get('plan_benefits', []):
        cursor.execute('''
            INSERT INTO plan_benefits (policy_product_code, claim_type, covered, waiting_period_days, annual_limit, per_claim_limit, lifetime_limit, deductible_annual, co_payment_pct, co_insurance_pct, co_insurance_cap, non_panel_reimbursement_pct, substance_abuse_covered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (pb['policy_product_code'], pb['claim_type'], pb['covered'], pb['waiting_period_days'], pb['annual_limit'], pb['per_claim_limit'], pb['lifetime_limit'], pb['deductible_annual'], pb['co_payment_pct'], pb['co_insurance_pct'], pb['co_insurance_cap'], pb['non_panel_reimbursement_pct'], pb['substance_abuse_covered']))

    # Insert claim utilisation
    for cu in db_pre_auth.get('claim_utilisation', []):
        cursor.execute('''
            INSERT INTO claim_utilisation (policy_no, claim_type, benefit_year, claim_reference_no, net_payable, status, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (cu['policy_no'], cu['claim_type'], cu['benefit_year'], cu['claim_reference_no'], cu['net_payable'], cu['status'], cu['posted_at']))

    # Insert clinical tables
    for item in db_clinical.get('icd10_reference', []):
        cursor.execute('INSERT INTO icd10_reference (code, description, status) VALUES (?, ?, ?)', 
                       (item['code'], item['description'], item['status']))
                       
    for item in db_clinical.get('cpt_reference', []):
        cursor.execute('INSERT INTO cpt_reference (code, description, status) VALUES (?, ?, ?)', 
                       (item['code'], item['description'], item['status']))
                       
    for item in db_clinical.get('icd10_cpt_plausibility', []):
        cursor.execute('INSERT INTO icd10_cpt_plausibility (icd10_code, cpt_code, plausible) VALUES (?, ?, ?)', 
                       (item['icd10_code'], item['cpt_code'], item['plausible']))
                       
    for item in db_clinical.get('medical_necessity_guidelines', []):
        cursor.execute('INSERT INTO medical_necessity_guidelines (icd10_code, cpt_code, necessity_confirmed) VALUES (?, ?, ?)', 
                       (item['icd10_code'], item['cpt_code'], item['necessity_confirmed']))
                       
    for item in db_clinical.get('rps_schedule', []):
        cursor.execute('INSERT INTO rps_schedule (cpt_code, provider_type, setting, unit_price) VALUES (?, ?, ?, ?)', 
                       (item['cpt_code'], item['provider_type'], item['setting'], item['unit_price']))
                       
    for item in db_clinical.get('exclusion_catalogue', []):
        cursor.execute('INSERT INTO exclusion_catalogue (exclusion_key, type, value) VALUES (?, ?, ?)', 
                       (item['exclusion_key'], item['type'], item['value']))
                       
    for item in db_pre_auth.get('pre_authorisations', []):
        cursor.execute('INSERT INTO pre_authorisations (pre_auth_no, policy_no, status, authorised_amount, expiry_date) VALUES (?, ?, ?, ?, ?)',
                       (item['pre_auth_no'], item['policy_no'], item['status'], item['authorised_amount'], item['expiry_date']))

    for item in db_providers.get('accredited_providers', []):
        cursor.execute('INSERT INTO accredited_providers (provider_registration, provider_name, provider_type, setting, panel_status, accreditation_expiry_date) VALUES (?, ?, ?, ?, ?, ?)',
                       (item['provider_registration'], item['provider_name'], item['provider_type'], item['setting'], item['panel_status'], item['accreditation_expiry_date']))

    for item in db_physicians.get('physician_registry', []):
        cursor.execute('INSERT INTO physician_registry (physician_license_no, physician_name, specialty, status, expiry_date) VALUES (?, ?, ?, ?, ?)',
                       (item['physician_license_no'], item['full_name'], item['specialty'], item['status'], item['expiry_date']))

    conn.commit()
    conn.close()
    print("Database fully initialized with Node 2, Node 3, and Node 4 data at", DB_PATH)

if __name__ == "__main__":
    init_db()
