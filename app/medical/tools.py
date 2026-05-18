"""
Node 4 tools — four distinct tool groups:

  1. MCP-simulated registry tools (registry.db) — provider accreditation & physician licence
  2. NLM Clinical Tables API — live ICD-10 code validation
  3. RPS schedule query (database.db) — benchmark pricing
  4. Pre-authorisations DB query (database.db) — pre-auth validation
"""
import sqlite3
import os
import requests
from datetime import date
from typing import Optional, Dict, Any, List

REGISTRY_DB = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'health-insurance-claim', 'synthetic data', 'registry.db')
DB_PATH     = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'health-insurance-claim', 'synthetic data', 'database.db')
CPT_DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cpt_reference.db')

# ─────────────────────────────────────────────────────────────────────────────
# GROUP 1 — MCP-simulated: Provider & Physician registry tools
# ─────────────────────────────────────────────────────────────────────────────

def mcp_lookup_provider(provider_registration: str) -> Optional[Dict[str, Any]]:
    """
    [MCP Tool] Queries the external MOH accredited provider registry
    (simulated via registry.db) using the provider's registration number.
    Returns accreditation metadata or None if not found.
    """
    conn = sqlite3.connect(REGISTRY_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM accredited_providers WHERE provider_registration = ?",
        (provider_registration,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def mcp_lookup_physician(physician_license_no: str) -> Optional[Dict[str, Any]]:
    """
    [MCP Tool] Queries the external Singapore Medical Council (SMC) physician
    licence registry (simulated via registry.db) using the MCR licence number.
    Returns physician metadata or None if not found.
    """
    conn = sqlite3.connect(REGISTRY_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM physician_registry WHERE physician_license_no = ?",
        (physician_license_no,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─────────────────────────────────────────────────────────────────────────────
# GROUP 2 — NLM Clinical Tables API — live ICD-10 lookup
# ─────────────────────────────────────────────────────────────────────────────

def nlm_validate_icd10(code: str) -> Dict[str, Any]:
    """
    Queries the NLM Clinical Tables ICD-10-CM search API to validate an ICD-10 code.
    Returns {valid: bool, description: str, source: str}
    """
    url = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
    try:
        resp = requests.get(url, params={"sf": "code,name", "terms": code, "maxList": 5}, timeout=10)
        data = resp.json()
        # data format: [count, [codes], null, [[code, name], ...]]
        matches = data[3] if len(data) > 3 and data[3] else []
        exact = [m for m in matches if m[0].upper() == code.upper()]
        if exact:
            return {"valid": True, "description": exact[0][1], "source": "NLM Clinical Tables ICD-10-CM API v3"}
        elif matches:
            return {"valid": False, "description": f"Code not found exactly; nearest: {matches[0][0]} ({matches[0][1]})", "source": "NLM Clinical Tables ICD-10-CM API v3"}
        else:
            return {"valid": False, "description": f"ICD-10 code {code} not found in NLM database", "source": "NLM Clinical Tables ICD-10-CM API v3"}
    except Exception as e:
        return {"valid": False, "description": f"NLM API error: {e}", "source": "NLM Clinical Tables ICD-10-CM API v3"}


# ─────────────────────────────────────────────────────────────────────────────
# GROUP 3 — RPS schedule benchmark query
# ─────────────────────────────────────────────────────────────────────────────

def get_rps_benchmark(cpt_codes: List[str], provider_type: str, setting: str) -> Dict[str, float]:
    """
    Queries rps_schedule for each CPT code to sum the benchmark price.
    Returns {cpt_code: unit_price, ..., "__total__": total}
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    result = {}
    total = 0.0
    for code in cpt_codes:
        row = conn.execute(
            "SELECT unit_price FROM rps_schedule WHERE cpt_code = ? AND provider_type = ? AND setting = ?",
            (code, provider_type, setting)
        ).fetchone()
        price = float(row['unit_price']) if row else 0.0
        result[code] = price
        total += price
    conn.close()
    result["__total__"] = total
    return result


# ─────────────────────────────────────────────────────────────────────────────
# GROUP 4 — Pre-authorisation DB query
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# GROUP 2b — CMS PFS CPT Reference lookup (authoritative code validity)
# ─────────────────────────────────────────────────────────────────────────────

def lookup_cpt_code(code: str) -> Dict[str, Any]:
    """
    Looks up a CPT/HCPCS code in the local CMS Physician Fee Schedule reference
    database (built from CMS 2024/2025 PFS RVU data). Returns whether the code
    is a valid, active CPT code, its official short description, and the source.
    """
    conn = sqlite3.connect(CPT_DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT hcpcs_code, short_descriptor, status_code, source FROM cpt_reference WHERE hcpcs_code = ?",
        (code.strip(),)
    ).fetchone()
    conn.close()
    if row:
        return {
            "found": True,
            "hcpcs_code": row["hcpcs_code"],
            "short_descriptor": row["short_descriptor"],
            "status_code": row["status_code"],
            "active": row["status_code"] == "A",
            "source": row["source"],
        }
    else:
        return {
            "found": False,
            "hcpcs_code": code,
            "short_descriptor": None,
            "status_code": None,
            "active": False,
            "source": "CMS PFS reference DB (code not found — may be unlisted, bundled, or invalid)",
        }


def get_pre_authorisation(pre_auth_no: str) -> Optional[Dict[str, Any]]:
    """Queries pre_authorisations table for a given pre-auth number."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM pre_authorisations WHERE pre_auth_no = ?",
        (pre_auth_no,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
