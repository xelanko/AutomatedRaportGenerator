"""
Validation layer:
  1. Schema validation (Pydantic) — types, required fields, ranges.
  2. Numerical verification — reconciliation of totals, outlier detection.
  3. Content evaluation — checks that generated report text stays
     consistent with the underlying numbers (used after report text is
     drafted, before export).
"""
import statistics
from typing import Iterable
import pandas as pd
import config
import logger_setup
from models import SalesRecord, FeedbackRecord, ValidationIssue

log = logger_setup.get_logger(__name__)


def validate_schema(raw_records: list[dict], model=SalesRecord) -> tuple[list, list[ValidationIssue]]:
    """Validate each raw dict against a Pydantic model. Returns (valid_objects, issues)."""
    valid, issues = [], []
    for rec in raw_records:
        try:
            valid.append(model(**rec))
        except Exception as e:
            issues.append(ValidationIssue(
                level="error",
                field=None,
                message=str(e),
                record_id=rec.get("record_id"),
            ))
    log.info(f"Schema validation: {len(valid)} valid, {len(issues)} rejected")
    return valid, issues


def detect_outliers_zscore(records: list[SalesRecord], field: str = "revenue",
                            threshold: float = None) -> list[ValidationIssue]:
    """Flag values whose z-score exceeds the configured threshold."""
    threshold = threshold or config.OUTLIER_Z_SCORE_THRESHOLD
    values = [getattr(r, field) for r in records]
    if len(values) < 2:
        return []

    mean = statistics.mean(values)
    stdev = statistics.pstdev(values) or 1e-9  # avoid divide-by-zero

    issues = []
    for r in records:
        z = (getattr(r, field) - mean) / stdev
        if abs(z) > threshold:
            issues.append(ValidationIssue(
                level="warning",
                field=field,
                message=f"Outlier detected: {field}={getattr(r, field)} (z-score={z:.2f})",
                record_id=r.record_id,
            ))
    log.info(f"Outlier detection on '{field}': {len(issues)} flagged")
    return issues


def reconcile_totals(records: list[SalesRecord], expected_total: float,
                      field: str = "revenue", tolerance: float = None) -> list[ValidationIssue]:
    """Cross-check that the sum of a field matches an externally expected total
    (e.g. from a source system's own report), within a tolerance %."""
    tolerance = tolerance if tolerance is not None else config.RECONCILIATION_TOLERANCE
    actual_total = sum(getattr(r, field) for r in records)
    if expected_total == 0:
        diff_pct = 0 if actual_total == 0 else 1
    else:
        diff_pct = abs(actual_total - expected_total) / abs(expected_total)

    issues = []
    if diff_pct > tolerance:
        issues.append(ValidationIssue(
            level="error",
            field=field,
            message=(f"Reconciliation mismatch: computed sum={actual_total:.2f}, "
                     f"expected={expected_total:.2f}, diff={diff_pct:.2%} "
                     f"(tolerance={tolerance:.2%})"),
        ))
    else:
        log.info(f"Reconciliation OK for '{field}': {actual_total:.2f} vs expected {expected_total:.2f}")
    return issues


def check_referential_integrity(records: list[SalesRecord], allowed_regions: Iterable[str],
                                 allowed_categories: Iterable[str]) -> list[ValidationIssue]:
    """Business-rule validation: values must belong to known reference sets."""
    issues = []
    allowed_regions = set(allowed_regions)
    allowed_categories = set(allowed_categories)
    for r in records:
        if r.region not in allowed_regions:
            issues.append(ValidationIssue(level="error", field="region",
                                           message=f"Unknown region '{r.region}'", record_id=r.record_id))
        if r.category not in allowed_categories:
            issues.append(ValidationIssue(level="error", field="category",
                                           message=f"Unknown category '{r.category}'", record_id=r.record_id))
    return issues


import re


def evaluate_generated_content(narrative_text: str, records: list[SalesRecord]) -> list[ValidationIssue]:
    """
    Sanity-checks any auto-generated narrative sentences against the real numbers,
    so the report text can't drift from the data (a common LLM-summary failure mode).
    Looks for numbers mentioned in the text and confirms they're within range of
    real aggregates.
    """
    issues = []
    total_revenue = sum(r.revenue for r in records)

    # Improved regex to match valid formatted numbers (e.g., 1,234.56, 1000, 45.5)
    raw_matches = re.findall(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b|\b\d+(?:\.\d+)?\b", narrative_text)

    numbers_in_text = []
    for match in raw_matches:
        try:
            numbers_in_text.append(float(match.replace(",", "")))
        except ValueError:
            continue

    if numbers_in_text and total_revenue > 0:
        closest = min(numbers_in_text, key=lambda n: abs(n - total_revenue))
        diff_pct = abs(closest - total_revenue) / total_revenue

        if diff_pct > 0.05:  # more than 5% off from the real total anywhere in the text
            issues.append(ValidationIssue(
                level="warning",
                message=(f"Generated narrative may misstate totals: closest mentioned "
                         f"number {closest:.2f} differs from actual total revenue "
                         f"{total_revenue:.2f} by {diff_pct:.1%}"),
            ))

    return issues


def summarize_issues(issues: list[ValidationIssue]) -> dict:
    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]
    return {"errors": len(errors), "warnings": len(warnings), "issues": issues}