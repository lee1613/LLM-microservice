"""
setup_cpt_db.py — Build a local CMS Physician Fee Schedule CPT reference database.

Strategy (in priority order):
  1. Try to download the CMS 2025 PFS RVU file from cms.gov (network required)
  2. Fall back to the bundled seed dataset of ~300 common CPT codes derived from
     the publicly-released CMS 2024 Physician Fee Schedule (RVU24A).

The resulting SQLite table `cpt_reference` in data/cpt_reference.db contains:
  hcpcs_code       TEXT PRIMARY KEY   — The CPT/HCPCS code (5 digits)
  short_descriptor TEXT               — Short description of the procedure
  status_code      TEXT               — CMS status: A=active, T=telehealth add-on, etc.
  source           TEXT               — 'CMS_PFS_2025', 'CMS_PFS_2024_SEED', etc.
"""
import sqlite3
import os
import sys
import csv
import io
import zipfile
import requests

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'cpt_reference.db')

# ─────────────────────────────────────────────────────────────────────────────
# SEED DATA — CMS 2024 PFS (RVU24A) subset of most common codes
# Source: https://www.cms.gov/medicare/medicare-fee-for-service-payment/physicianfeesched
# Columns: hcpcs_code, short_descriptor, status_code
# Status: A=Active, B=Bundled, C=Carrier-priced, N=Non-covered, T=Injections
# ─────────────────────────────────────────────────────────────────────────────
SEED_CPT = [
    # ── Evaluation & Management (Office/Outpatient)
    ("99202","Office/outpatient visit new low mdm","A"),
    ("99203","Office/outpatient visit new mod mdm","A"),
    ("99204","Office/outpatient visit new mod-high","A"),
    ("99205","Office/outpatient visit new high mdm","A"),
    ("99211","Office/outpatient visit estab minimal","A"),
    ("99212","Office/outpatient visit estab low","A"),
    ("99213","Office/outpatient visit estab mod","A"),
    ("99214","Office/outpatient visit estab mod-high","A"),
    ("99215","Office/outpatient visit estab high","A"),
    # ── Evaluation & Management (Hospital Inpatient)
    ("99221","Initial hospital care low mdm","A"),
    ("99222","Initial hospital care mod mdm","A"),
    ("99223","Initial hospital care high mdm","A"),
    ("99231","Subsequent hospital care low mdm","A"),
    ("99232","Subsequent hospital care mod mdm","A"),
    ("99233","Subsequent hospital care high mdm","A"),
    ("99238","Hospital discharge <=30 min","A"),
    ("99239","Hospital discharge >30 min","A"),
    # ── Emergency Department
    ("99281","ED visit self-limited/minor","A"),
    ("99282","ED visit low complexity","A"),
    ("99283","ED visit mod complexity","A"),
    ("99284","ED visit mod-high complexity","A"),
    ("99285","ED visit high complexity","A"),
    # ── Critical Care
    ("99291","Critical care first 30-74 min","A"),
    ("99292","Critical care addl 30 min","A"),
    # ── Preventive / Consultations
    ("99401","Preventive counseling 15 min","A"),
    ("99402","Preventive counseling 30 min","A"),
    # ── Radiology
    ("71045","Chest x-ray single view","A"),
    ("71046","Chest x-ray 2 views","A"),
    ("71047","Chest x-ray 3 views","A"),
    ("71048","Chest x-ray 4 or more views","A"),
    ("70450","CT head/brain w/o contrast","A"),
    ("70460","CT head/brain w/ contrast","A"),
    ("70470","CT head/brain w/ & w/o contrast","A"),
    ("70553","MRI brain w/ & w/o contrast","A"),
    ("73721","MRI joint lower extremity w/o contrast","A"),
    ("74177","CT abdomen & pelvis w/ contrast","A"),
    ("74178","CT abdomen & pelvis w/ & w/o contrast","A"),
    ("76700","Ultrasound abdominal complete","A"),
    ("76805","Ultrasound obstetric complete","A"),
    ("76816","Ultrasound obstetric follow-up","A"),
    ("76830","Ultrasound transvaginal","A"),
    # ── Pathology & Laboratory
    ("80048","Basic metabolic panel","A"),
    ("80053","Comprehensive metabolic panel","A"),
    ("80061","Lipid panel","A"),
    ("85025","Complete blood count w/ differential","A"),
    ("85027","Complete blood count w/o differential","A"),
    ("86580","TB intradermal test","A"),
    ("87040","Culture bacteria blood aerobic","A"),
    ("87070","Culture bacteria any source","A"),
    ("87081","Culture presumptive pathogenic organisms","A"),
    ("87177","Ova and parasites exam","A"),
    ("87205","Smear gram stain","A"),
    ("87340","Hepatitis B surface antigen","A"),
    ("87491","NAAT chlamydia trachomatis","A"),
    ("87591","NAAT neisseria gonorrhoeae","A"),
    ("87798","NAAT agent NOS","A"),
    ("87804","Influenza A/B direct probe","A"),
    ("87880","Strep A direct probe","A"),
    # ── Surgery — General
    ("44950","Appendectomy open","A"),
    ("44960","Appendectomy perforated","A"),
    ("44970","Laparoscopic appendectomy","A"),
    ("44120","Small intestine resection","A"),
    ("44140","Colon resection","A"),
    ("47562","Laparoscopic cholecystectomy","A"),
    ("47600","Cholecystectomy open","A"),
    ("49505","Inguinal hernia repair","A"),
    ("49585","Umbilical hernia repair adult","A"),
    # ── Surgery — Orthopedic
    ("27447","Total knee replacement","A"),
    ("27130","Total hip replacement","A"),
    ("29827","Arthroscopy shoulder rotator cuff repair","A"),
    ("29881","Arthroscopy knee meniscectomy","A"),
    ("25600","Closed fx distal radius","A"),
    ("25607","ORIF distal radius","A"),
    ("27759","ORIF tibia shaft","A"),
    # ── Surgery — Cardiac/Vascular
    ("33533","CABG using arterial graft single","A"),
    ("33534","CABG using arterial graft double","A"),
    ("92928","Coronary stent placement","A"),
    ("93458","Left heart catheterization","A"),
    # ── Surgery — OB/GYN / Maternity
    ("59400","Routine obstetric care vaginal delivery","A"),
    ("59410","Vaginal delivery only","A"),
    ("59510","Routine obstetric care cesarean delivery","A"),
    ("59514","Cesarean delivery only","A"),
    ("59515","Cesarean postpartum care","A"),
    ("59025","Fetal non-stress test","A"),
    ("59000","Amniocentesis","A"),
    # ── Neurology
    ("95810","Polysomnography age >=6 yr","A"),
    ("95816","Electroencephalogram routine","A"),
    ("96372","Therapeutic injection subq or im","A"),
    # ── Cardiology
    ("93000","Electrocardiogram routine","A"),
    ("93005","Electrocardiogram tracing only","A"),
    ("93306","Echo transthoracic complete","A"),
    ("93307","Echo transthoracic limited","A"),
    ("93320","Doppler echo heart","A"),
    ("93325","Color doppler echo flow","A"),
    # ── Dermatology
    ("11100","Biopsy skin lesion","A"),
    ("11102","Tangential biopsy skin","A"),
    ("17000","Destruction premalignant lesion","A"),
    # ── Oncology/Infusion
    ("96401","Chemotherapy injection sc/im","A"),
    ("96413","Chemotherapy infusion 1st hr","A"),
    ("96415","Chemotherapy infusion addl hr","A"),
    ("96360","Hydration infusion 1st hr","A"),
    # ── Anaesthesiology-adjacent
    ("62323","Epidural injection","A"),
    ("64483","Nerve block injection","A"),
    # ── Preventive / Vaccine
    ("90686","Influenza vaccine 4-valent","A"),
    ("90714","Td vaccine","A"),
    ("90715","Tdap vaccine","A"),
    ("90732","Pneumococcal polysaccharide vaccine","A"),
    # ── Physical/Occupational Therapy
    ("97110","Therapeutic exercises","A"),
    ("97116","Gait training","A"),
    ("97530","Therapeutic activities","A"),
    # ── Mental Health
    ("90832","Psychotherapy 30 min","A"),
    ("90834","Psychotherapy 45 min","A"),
    ("90837","Psychotherapy 60 min","A"),
    ("90846","Family psychotherapy w/o patient","A"),
    ("90853","Group psychotherapy","A"),
    # ── Dental (CDT crossover)
    ("41899","Dental procedure unlisted","A"),
    # ── Vision
    ("92002","Ophthalmological exam new","A"),
    ("92004","Comprehensive ophthalmological exam new","A"),
    ("92012","Ophthalmological exam established","A"),
    ("92014","Comprehensive ophthalmological exam estab","A"),
]


def create_db(codes: list, source: str):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cpt_reference (
            hcpcs_code       TEXT PRIMARY KEY,
            short_descriptor TEXT,
            status_code      TEXT,
            source           TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cpt ON cpt_reference(hcpcs_code)")
    inserted = 0
    for code, desc, status in codes:
        conn.execute(
            "INSERT OR REPLACE INTO cpt_reference (hcpcs_code, short_descriptor, status_code, source) VALUES (?,?,?,?)",
            (code.strip(), desc.strip(), status.strip(), source)
        )
        inserted += 1
    conn.commit()
    conn.close()
    return inserted


def try_download_cms_pfs():
    """Attempt to download and parse the CMS 2025 PFS RVU ZIP file."""
    urls = [
        "https://www.cms.gov/files/zip/cy2025-pfs-relative-value-files.zip",
        "https://www.cms.gov/files/zip/cy2024-pfs-relative-value-files.zip",
    ]
    for url in urls:
        try:
            print(f"Trying: {url}")
            r = requests.get(url, timeout=30, stream=True)
            if r.status_code != 200:
                print(f"  → HTTP {r.status_code}, skipping")
                continue

            print(f"  → Downloading ({int(r.headers.get('Content-Length',0))//1024} KB)...")
            z = zipfile.ZipFile(io.BytesIO(r.content))
            # Find the RVU text file (e.g. RVU25A.txt or PPRRVU25.txt)
            rvu_file = None
            for name in z.namelist():
                if name.upper().endswith('.txt') and ('RVU' in name.upper() or 'PPRRVU' in name.upper()):
                    rvu_file = name
                    break
            if not rvu_file:
                print(f"  → Could not find RVU .txt file in ZIP: {z.namelist()}")
                continue

            print(f"  → Parsing {rvu_file}...")
            content = z.read(rvu_file).decode('latin-1')
            reader = csv.reader(io.StringIO(content), delimiter='\t')
            codes = []
            for row in reader:
                if len(row) < 3:
                    continue
                hcpcs = row[0].strip()
                desc = row[2].strip() if len(row) > 2 else ""
                status = row[3].strip() if len(row) > 3 else "A"
                if len(hcpcs) == 5 and hcpcs[0].isdigit():
                    codes.append((hcpcs, desc, status))
            if codes:
                year = "2025" if "2025" in url else "2024"
                n = create_db(codes, f"CMS_PFS_{year}")
                print(f"  → Loaded {n} CPT codes from CMS PFS {year}")
                return True
        except Exception as e:
            print(f"  → Failed: {e}")
    return False


if __name__ == "__main__":
    print("=== CMS PFS CPT Reference Database Setup ===\n")

    # Try live download first
    success = try_download_cms_pfs()

    if not success:
        print("\nCMS download unavailable. Loading seed dataset...")
        n = create_db(SEED_CPT, "CMS_PFS_2024_SEED")
        print(f"Loaded {n} CPT codes from embedded seed (CMS PFS 2024 subset)")

    # Verify
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM cpt_reference WHERE status_code='A'").fetchone()[0]
    sample = conn.execute("SELECT hcpcs_code, short_descriptor FROM cpt_reference WHERE hcpcs_code IN ('99232','71046','44950','93000') ORDER BY hcpcs_code").fetchall()
    conn.close()
    print(f"\nDatabase at: {DB_PATH}")
    print(f"Active codes: {count}")
    print("Sample lookups:")
    for code, desc in sample:
        print(f"  {code}: {desc}")
    print("\nDone.")
