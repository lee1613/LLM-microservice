"""
Reset the database to its original seed state before a clean pipeline run.
Removes all rows added by test runs, restores claim_sequence to 1101.
"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/health-insurance-claim/synthetic data/database.db'
conn = sqlite3.connect(DB)

# 1. Remove all test-run deductible_ledger rows (keep seed rows, i.e. those with _comment)
conn.execute("DELETE FROM deductible_ledger WHERE _comment IS NULL")
print("deductible_ledger: removed test rows")

# 2. Remove claims written by tests (keep the B005 seed row CLM-2025-0000877)
conn.execute("DELETE FROM claims WHERE claim_reference_draft LIKE 'DRAFT-2026%'")
print("claims: removed test rows")

# 3. Reset claim_sequence back to 1101
conn.execute("UPDATE claim_sequence SET next_val = 1101 WHERE year = '2025'")
print("claim_sequence: reset to 1101")

# 4. Remove claim_utilisation rows written by tests
conn.execute("DELETE FROM claim_utilisation WHERE claim_reference_no LIKE 'DRAFT-2026%' OR claim_reference_no LIKE 'CLM-2025-0001%'")
print("claim_utilisation: removed test rows")

conn.commit()

# Verify
print("\n--- deductible_ledger (post-reset) ---")
for r in conn.execute("SELECT policy_no, benefit_year, amount, claim_reference_no FROM deductible_ledger").fetchall():
    print(" ", tuple(r))

print("\n--- claim_sequence ---")
for r in conn.execute("SELECT * FROM claim_sequence").fetchall():
    print(" ", tuple(r))

print("\n--- claims ---")
for r in conn.execute("SELECT claim_reference_draft, claim_reference_no, status FROM claims").fetchall():
    print(" ", tuple(r))

conn.close()
print("\nDB reset complete.")
