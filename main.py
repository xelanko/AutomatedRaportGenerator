"""
CLI entry point. Run:
  python main.py generate      -> generate the report once, immediately
  python main.py schedule      -> generate on a recurring schedule
  python main.py setup-sample  -> create sample CSV/SQL/text data for a quick demo
"""
import sys
from datetime import date
from pathlib import Path
import config
import logger_setup
from data_sources import csv_source, sql_source, text_source
from pipeline import run_pipeline
from scheduler import schedule_job
from benchmark import timed

log = logger_setup.get_logger(__name__)

SAMPLE_CSV = config.DATA_DIR / "sales.csv"
SAMPLE_TEXT_DIR = config.DATA_DIR / "feedback"


def setup_sample_data():
    SAMPLE_TEXT_DIR.mkdir(exist_ok=True)

    SAMPLE_CSV.write_text(
        "date,region,category,revenue,quantity\n"
        "2025-06-01,North,Electronics,12000.50,34\n"
        "2025-06-02,South,Furniture,8000.00,12\n"
        "2025-06-03,East,Electronics,15500.75,41\n"
        "2025-06-04,West,Clothing,3000.25,60\n"
        "2025-06-05,North,Furniture,500000.00,3\n"  # intentional outlier
        "2025-06-06,South,Electronics,9800.10,28\n"
    )

    (SAMPLE_TEXT_DIR / "review1.txt").write_text(
        "2025-06-02 - North region customer: The delivery was great and support was helpful."
    )
    (SAMPLE_TEXT_DIR / "review2.txt").write_text(
        "2025-06-04 - South region customer: Product arrived broken, terrible experience."
    )

    sql_source.create_sample_table_and_data()
    log.info("Sample data created in ./data")


@timed
def generate_report_once():
    csv_records = csv_source.extract(SAMPLE_CSV)
    sql_records = sql_source.extract()
    all_records = csv_records + sql_records

    result = run_pipeline(
        raw_records=all_records,
        report_title="Monthly Sales Report",
        period_start=date(2025, 6, 1),
        period_end=date(2025, 6, 30),
        allowed_regions={"North", "South", "East", "West"},
        allowed_categories={"Electronics", "Furniture", "Clothing"},
        expected_total_revenue=None,  # set this if you have an authoritative external total
    )

    print(f"\nPDF report:   {result['pdf_path']}")
    print(f"Excel report: {result['xlsx_path']}")
    print(f"Validation issues: {len(result['issues'])}")
    for issue in result["issues"]:
        print(f"  [{issue.level.upper()}] {issue.message}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]
    if command == "setup-sample":
        setup_sample_data()
    elif command == "generate":
        generate_report_once()
    elif command == "schedule":
        schedule_job(generate_report_once)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()