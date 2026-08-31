import pytest
from datetime import date
from models import SalesRecord
import validators


@pytest.fixture
def sample_records():
    return [
        SalesRecord(record_id="1", record_date=date(2025, 6, 1), region="North",
                    category="Electronics", revenue=1000, quantity=10, source="test"),
        SalesRecord(record_id="2", record_date=date(2025, 6, 2), region="South",
                    category="Furniture", revenue=1100, quantity=12, source="test"),
        SalesRecord(record_id="3", record_date=date(2025, 6, 3), region="East",
                    category="Electronics", revenue=50000, quantity=5, source="test"),  # outlier
    ]


def test_schema_validation_rejects_bad_records():
    raw = [{"record_id": "x", "record_date": "2025-06-01", "region": "North",
            "category": "Electronics", "revenue": -50, "quantity": 5, "source": "test"}]
    valid, issues = validators.validate_schema(raw)
    assert len(valid) == 0
    assert len(issues) == 1
    assert issues[0].level == "error"


def test_outlier_detection_flags_extreme_value(sample_records):
    issues = validators.detect_outliers_zscore(sample_records, field="revenue", threshold=1.0)
    assert any("50000" in i.message for i in issues)


def test_reconciliation_passes_within_tolerance(sample_records):
    total = sum(r.revenue for r in sample_records)
    issues = validators.reconcile_totals(sample_records, expected_total=total, tolerance=0.01)
    assert issues == []


def test_reconciliation_fails_outside_tolerance(sample_records):
    issues = validators.reconcile_totals(sample_records, expected_total=1.0, tolerance=0.01)
    assert len(issues) == 1
    assert issues[0].level == "error"


def test_referential_integrity_flags_unknown_region(sample_records):
    issues = validators.check_referential_integrity(
        sample_records, allowed_regions={"North", "South"}, allowed_categories={"Electronics", "Furniture"})
    assert any("East" in i.message for i in issues)


def test_evaluate_generated_content_flags_wrong_numbers(sample_records):
    bad_narrative = "Total revenue was 9,999,999 across all regions."
    issues = validators.evaluate_generated_content(bad_narrative, sample_records)
    assert len(issues) == 1