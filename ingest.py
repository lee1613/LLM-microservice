import json
import sqlite3
import os

def insert_json_to_db(json_file, db_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    for table_name, rows in data.items():
        if table_name.startswith('_'):
            continue # skip comments
        if not isinstance(rows, list):
            continue
        if not rows:
            continue
        
        # Get all columns (preserve order from first element as much as possible)
        columns = list(rows[0].keys())
        for row in rows:
            for k in row.keys():
                if k not in columns:
                    columns.append(k)
        
        # Create table
        cols_def = ", ".join([f'"{col}" TEXT' for col in columns])
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        cursor.execute(f'CREATE TABLE "{table_name}" ({cols_def})')
        
        # Insert data
        for row in rows:
            placeholders = ", ".join(["?" for _ in columns])
            values = [row.get(col) for col in columns] # keep native type so sqlite can handle int/float/null appropriately
            cols_str = ", ".join([f'"{c}"' for c in columns])
            cursor.execute(f'INSERT INTO "{table_name}" ({cols_str}) VALUES ({placeholders})', values)
            
    conn.commit()
    conn.close()

base_dir = r"c:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\LLM-microservice\data\health-insurance-claim\synthetic data"

# We will put the DBs directly in the synthetic data folder
db1_path = os.path.join(base_dir, "database.db")
db2_path = os.path.join(base_dir, "registry.db")

# Delete if exist
if os.path.exists(db1_path): os.remove(db1_path)
if os.path.exists(db2_path): os.remove(db2_path)

db1_files = [
    "db_policies.json",
    "db_clinical.json",
    "db_plan_documents.json",
    "db_pre_auth_utilisation_ledger.json"
]

for f in db1_files:
    p = os.path.join(base_dir, f)
    if os.path.exists(p):
        insert_json_to_db(p, db1_path)
        print(f"Ingested {f} into database.db")

db2_file = "db_provider_and_physician_registry.json"
p2 = os.path.join(base_dir, db2_file)
if os.path.exists(p2):
    insert_json_to_db(p2, db2_path)
    print(f"Ingested {db2_file} into registry.db")
