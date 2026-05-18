"""
Test reachable CPT lookup options
"""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

tests = [
    ("NLM ICD-10",     "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?sf=code,name&terms=J18.9&maxList=2"),
    ("VSAC FHIR CPT",  "https://cts.nlm.nih.gov/fhir/CodeSystem/2.16.840.1.113883.6.12"),
    ("NLM FHIR CPT",   "https://clinicaltables.nlm.nih.gov/fhir/R4/CodeSystem?url=http://www.ama-assn.org/go/cpt"),
    ("OpenFDA drug",   "https://api.fda.gov/drug/label.json?limit=1"),
    ("GitHub NLM snomed","https://clinicaltables.nlm.nih.gov/api/snomed/v3/search?sf=code,display&terms=233604007&maxList=2"),
]

for name, url in tests:
    try:
        r = requests.get(url, timeout=8)
        print(f"{name}: {r.status_code} | {r.text[:100]}")
    except Exception as e:
        print(f"{name}: ERROR — {e}")
