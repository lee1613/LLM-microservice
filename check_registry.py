import sqlite3, json, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/health-insurance-claim/synthetic data/registry.db')
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [r[0] for r in rows])
for table in [r[0] for r in rows]:
    sample = conn.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()
    if sample:
        print(f"\n--- {table} ---")
        print(dict(sample))
