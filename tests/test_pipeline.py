from datetime import date
from pipeline import run_pipeline, generate_narrative
from models import SalesRecord


def make_raw_records():
    return [
        {"record_id": "1", "record_date": "2025-06-01", "region": "North",
         "category": "Electronics", "revenue": 1000, "quantity": 10, "source": "test"},
        {"record_id": "2", "record_date": "2025-06-02", "region": "South",
         "category": "Furniture", "revenue": 1200, "quantity": 8, "source": "test"},
    ]


def test_narrative_mentions_real_total():
    records = [
        SalesRecord(record_id="1", record_date=date(2025, 6, 1), region="North",
                    category="Electronics", revenue=1000, quantity=10, source="test"),
        SalesRecord(record_id="2", record_date=date(2025, 6, 2), region="South",
                    category="Furniture", revenue=1200, quantity=8, source="test"),
    ]
    narrative = generate_narrative(records)
    assert "2,200" in narrative or "2200" in narrative


def test_full_pipeline_end_to_end(tmp_path, monkeypatch):
    import config
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path)
    (tmp_path / "charts").mkdir(exist_ok=True)

    result = run_pipeline(
        raw_records=make_raw_records(),
        report_title="Test Report",
        period_start=date(2025, 6, 1),
        period_end=date(2025, 6, 30),
        allowed_regions={"North", "South"},
        allowed_categories={"Electronics", "Furniture"},
    )

    assert result["pdf_path"].exists()
    assert result["xlsx_path"].exists()
    assert result["metadata"].total_records == 2