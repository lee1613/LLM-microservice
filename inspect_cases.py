import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'data/health-insurance-claim/synthetic data'
for f in sorted(os.listdir(base)):
    if f.endswith('_full_pipeline.json'):
        d = json.load(open(os.path.join(base, f), encoding='utf-8'))
        s = d.get('stage_1_intake', {}).get('_input', {})
        print(f"\n=== {f} ===")
        print(f"  claimant_name    : {s.get('claimant_name')}")
        print(f"  claim_type       : {s.get('claim_type')}")
        print(f"  claim_amount     : {s.get('claim_amount_requested')}")
        print(f"  policy_no        : {s.get('policy_no')}")
        print(f"  provider_reg     : {s.get('provider_registration')}")
