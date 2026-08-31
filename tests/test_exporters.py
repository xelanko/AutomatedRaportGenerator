from datetime import date, datetime
from pathlib import Path
from models import SalesRecord, ReportMetadata
from exporters.pdf_exporter import build_pdf_report
from exporters.excel_exporter import build_excel_report


def sample_records():
    return [
        SalesRecord(record_id="1", record_date=date(2025, 6, 1), region="North",
                    category="Electronics", revenue=1000, quantity=10, source="test"),
    ]


def sample_metadata():
    return ReportMetadata(
        title="Unit Test Report",
        period_start=date(2025, 6, 1),
        period_end=date(2025, 6, 30),
        total_records=1,
        generated_at=datetime.now(),
    )


def test_pdf_export_creates_file(tmp_path):
    out = tmp_path / "report.pdf"
    build_pdf_report(out, sample_metadata(), sample_records(), "Sample narrative text.", [])
    assert out.exists()
    assert out.stat().st_size > 0


def test_excel_export_creates_file(tmp_path):
    out = tmp_path / "report.xlsx"
    build_excel_report(out, sample_metadata(), sample_records())
    assert out.exists()
    assert out.stat().st_size > 0