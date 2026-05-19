import json
import os
import tempfile
import shutil
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import ValidationError

from app.intake.schemas import ClaimIntakeInput, ClaimIntakeOutput
from app.intake.agent import process_claim_intake

router = APIRouter(prefix="/intake", tags=["claim-intake"])


@router.post("/process", response_model=ClaimIntakeOutput)
async def intake_claim(
    claim_data: str = Form(
        ...,
        description=(
            "JSON string containing all claim metadata fields "
            "(policy_no, claimant_name, claim_type, etc.). "
            "If files are also attached, scanned_files in this JSON is ignored "
            "and the uploaded files are used instead."
        ),
    ),
    files: List[UploadFile] = File(
        default=[],
        description=(
            "The actual supporting PDF documents "
            "(e.g. medical_bill.pdf, discharge_summary.pdf, pre_auth_approval.pdf). "
            "When provided, the server reads these directly; "
            "scanned_files paths in claim_data are ignored."
        ),
    ),
):
    """
    Unified claim intake endpoint.

    Accepts **multipart/form-data** with two parts:

    - ``claim_data`` — a JSON string of all claim metadata fields.
    - ``files`` *(optional)* — the actual PDF documents to extract clinical data from.
      When files are uploaded, ``scanned_files`` inside ``claim_data`` is ignored and
      the uploaded bytes are used instead. When no files are attached, ``scanned_files``
      must contain valid server-side relative paths (e.g. ``B001/medical_bill.pdf``).

    **Example — uploading real PDFs (Python requests):**

    .. code-block:: python

        import requests, json

        metadata = {
            "policy_no": "HIC-2024-00123",
            "claimant_name": "Tan Wei Ming",
            "claimant_relationship": "self",
            "id_document_type": "nric",
            "id_document_no": "S7801234A",
            "date_of_birth": "1978-03-22",
            "incident_date": "2025-04-10",
            "claim_date": "2025-04-14",
            "claim_type": "hospitalisation",
            "claim_amount_requested": 18500.0,
            "provider_name": "Singapore General Hospital",
            "provider_registration": "MOH-HOSP-00142",
            "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
        }

        resp = requests.post(
            "http://139.180.136.212/intake/process",
            data={"claim_data": json.dumps(metadata)},
            files=[
                ("files", ("medical_bill.pdf",     open("medical_bill.pdf",     "rb"), "application/pdf")),
                ("files", ("discharge_summary.pdf", open("discharge_summary.pdf", "rb"), "application/pdf")),
                ("files", ("pre_auth_approval.pdf", open("pre_auth_approval.pdf", "rb"), "application/pdf")),
            ],
        )
        n1_output = resp.json()

    **Example — server-side paths only (no file upload):**

    .. code-block:: python

        metadata["scanned_files"] = [
            "B001/medical_bill.pdf",
            "B001/discharge_summary.pdf",
            "B001/pre_auth_approval.pdf",
        ]
        resp = requests.post(
            "http://139.180.136.212/intake/process",
            data={"claim_data": json.dumps(metadata)},
        )
    """
    # ── 1. Parse claim metadata ───────────────────────────────────────────────
    try:
        claim_dict = json.loads(claim_data)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"claim_data is not valid JSON: {exc}")

    # ── 2. Handle uploaded PDFs ───────────────────────────────────────────────
    tmp_dir: Optional[str] = None
    if files:
        tmp_dir = tempfile.mkdtemp(prefix="intake_upload_")
        scanned_paths: List[str] = []
        try:
            for upload in files:
                safe_name = os.path.basename(upload.filename or "document.pdf")
                dest = os.path.join(tmp_dir, safe_name)
                contents = await upload.read()
                with open(dest, "wb") as fh:
                    fh.write(contents)
                # parse_pdf_file_tool accepts absolute paths for uploaded files
                scanned_paths.append(dest)

            # Override scanned_files with the temp absolute paths
            claim_dict["scanned_files"] = scanned_paths

            # ── 3. Validate & run intake agent (files in scope) ───────────────
            try:
                structured_input = ClaimIntakeInput(**claim_dict)
            except (ValidationError, Exception) as exc:
                raise HTTPException(status_code=422, detail=str(exc))

            output = process_claim_intake(structured_input)

        finally:
            # Always clean up temp files
            shutil.rmtree(tmp_dir, ignore_errors=True)

    else:
        # ── No files uploaded — use scanned_files paths from claim_data ───────
        try:
            structured_input = ClaimIntakeInput(**claim_dict)
        except (ValidationError, Exception) as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        output = process_claim_intake(structured_input)

    return output
