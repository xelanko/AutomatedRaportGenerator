"""Upload a custom CSV to use as a data source for future jobs."""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

import config
from api.config import get_settings
from api.security import require_api_key
from api.schemas import UploadResponse

router = APIRouter(prefix="/data", tags=["data"], dependencies=[Depends(require_api_key)])
REQUIRED_COLUMNS = {"date", "region", "category", "revenue", "quantity"}


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    settings = get_settings()
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only .csv files are accepted")

    raw = await file.read()
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb}MB limit")

    text = raw.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(400, "CSV appears to be empty")

    missing = REQUIRED_COLUMNS - {c.strip().lower() for c in reader.fieldnames}
    if missing:
        raise HTTPException(400, f"CSV missing required columns: {missing}")

    rows = list(reader)
    dest = config.DATA_DIR / file.filename
    dest.write_text(text, encoding="utf-8")
    return UploadResponse(filename=file.filename, rows_detected=len(rows), saved_to=str(dest))