"""
Structured data source: Excel workbooks (any sheet).
"""
from pathlib import Path
import pandas as pd
import logger_setup

log = logger_setup.get_logger(__name__)


def extract(xlsx_path: Path, sheet_name=0) -> list[dict]:
    log.info(f"Extracting Excel data from {xlsx_path} (sheet={sheet_name})")
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Excel file not found: {xlsx_path}")

    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, engine="openpyxl")
    df.columns = [c.strip().lower() for c in df.columns]

    required = {"date", "region", "category", "revenue", "quantity"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Excel sheet missing required columns: {missing}")

    records = []
    for i, row in df.iterrows():
        records.append({
            "record_id": f"xlsx-{i}",
            "record_date": row["date"],
            "region": row["region"],
            "category": row["category"],
            "revenue": row["revenue"],
            "quantity": row["quantity"],
            "source": "excel",
        })
    log.info(f"Extracted {len(records)} records from Excel")
    return records