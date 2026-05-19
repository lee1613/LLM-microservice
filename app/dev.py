from fastapi import APIRouter
import sqlite3
import os

router = APIRouter(prefix="/dev", tags=["dev"])

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'health-insurance-claim', 'synthetic data', 'database.db')

@router.post("/reset")
def reset_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM deductible_ledger WHERE _comment IS NULL")
    conn.execute("DELETE FROM claims WHERE claim_reference_draft LIKE 'DRAFT-2026%'")
    conn.execute("UPDATE claim_sequence SET next_val = 1101 WHERE year = '2025'")
    conn.execute("DELETE FROM claim_utilisation WHERE claim_reference_no LIKE 'DRAFT-2026%' OR claim_reference_no LIKE 'CLM-2025-0001%'")
    conn.commit()
    conn.close()
    return {"status": "reset_complete"}
