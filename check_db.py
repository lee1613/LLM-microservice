import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/health-insurance-claim/synthetic data/database.db')
conn.row_factory = sqlite3.Row
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

for t in ['claim_sequence', 'claims']:
    print(f"\n--- {t} ---")
    rows = conn.execute(f"SELECT * FROM {t} LIMIT 2").fetchall()
    for r in rows: print(dict(r))

# Check accredited_providers (in registry.db)
conn2 = sqlite3.connect('data/health-insurance-claim/synthetic data/registry.db')
conn2.row_factory = sqlite3.Row
r = conn2.execute("SELECT provider_registration, bank_name, bank_account_no, bank_branch_code FROM accredited_providers LIMIT 3").fetchall()
print("\n--- accredited_providers (bank details) ---")
for row in r: print(dict(row))
