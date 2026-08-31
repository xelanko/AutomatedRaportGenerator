"""
Structured data source: CSV files.
"""
from pathlib import Path
import pandas as pd
import logger_setup

log = logger_setup.get_logger(__name__)


def extract(csv_path: Path) -> list[dict]:
    log.info(f"Extracting CSV data from {csv_path}")
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]

    required = {"date", "region", "category", "revenue", "quantity"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    records = []
    for i, row in df.iterrows():
        records.append({
            "record_id": f"csv-{i}",
            "record_date": row["date"],
            "region": row["region"],
            "category": row["category"],
            "revenue": row["revenue"],
            "quantity": row["quantity"],
            "source": "csv",
        })
    log.info(f"Extracted {len(records)} records from CSV")
    return records