"""
Orchestrates the full pipeline: extract -> validate -> generate narrative
-> chart -> export (PDF + Excel).
"""
from datetime import date, datetime
from pathlib import Path
import config
import logger_setup
from models import SalesRecord, ReportMetadata
import validators
import charts
from exporters.pdf_exporter import build_pdf_report
from exporters.excel_exporter import build_excel_report

log = logger_setup.get_logger(__name__)




def generate_narrative(records: list[SalesRecord]) -> str:
    """Simple templated narrative generation from real aggregates
    (swap this function for an LLM call if you want richer prose —
    just make sure to run evaluate_generated_content() on the output)."""
    total_revenue = sum(r.revenue for r in records)
    total_qty = sum(r.quantity for r in records)
    top_category = max(
        {r.category for r in records},
        key=lambda c: sum(r.revenue for r in records if r.category == c)
    )
    return (
        f"During the reporting period, total revenue reached {total_revenue:,.2f} "
        f"across {len(records)} transactions, with {total_qty} units sold. "
        f"The top-performing category was '{top_category}'."
    )


def run_pipeline(raw_records: list[dict], report_title: str,
                  period_start: date, period_end: date,
                  allowed_regions=None, allowed_categories=None,
                  expected_total_revenue: float = None) -> dict:
    log.info("=== Pipeline started ===")

    # 1. Schema validation
    valid_records, schema_issues = validators.validate_schema(raw_records, model=SalesRecord)

    # 2. Business rule validation
    business_issues = []
    if allowed_regions and allowed_categories:
        business_issues = validators.check_referential_integrity(
            valid_records, allowed_regions, allowed_categories)

    # 3. Numerical verification
    outlier_issues = validators.detect_outliers_zscore(valid_records, field="revenue")
    reconciliation_issues = []
    if expected_total_revenue is not None:
        reconciliation_issues = validators.reconcile_totals(
            valid_records, expected_total_revenue, field="revenue")

    all_issues = schema_issues + business_issues + outlier_issues + reconciliation_issues

    # 4. Narrative generation + content evaluation
    narrative = generate_narrative(valid_records)
    content_issues = validators.evaluate_generated_content(narrative, valid_records)
    all_issues += content_issues

    summary = validators.summarize_issues(all_issues)
    log.info(f"Validation summary: {summary['errors']} errors, {summary['warnings']} warnings")

    # 5. Charts
    chart_dir = config.OUTPUT_DIR / "charts"
    chart_dir.mkdir(exist_ok=True)
    chart_paths = [
        charts.revenue_by_category_bar(valid_records, chart_dir / "revenue_by_category.png"),
        charts.revenue_trend_line(valid_records, chart_dir / "revenue_trend.png"),
        charts.region_share_pie(valid_records, chart_dir / "region_share.png"),
    ]

    # 6. Metadata + export
    metadata = ReportMetadata(
        title=report_title,
        period_start=period_start,
        period_end=period_end,
        total_records=len(valid_records),
        validation_error_count=summary["errors"],
        validation_warning_count=summary["warnings"],
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = report_title.replace(' ', '_')
    pdf_path = config.OUTPUT_DIR / f"{safe_title}_{timestamp}.pdf"
    xlsx_path = config.OUTPUT_DIR / f"{safe_title}_{timestamp}.xlsx"

    build_pdf_report(pdf_path, metadata, valid_records, narrative, chart_paths, all_issues)
    build_excel_report(xlsx_path, metadata, valid_records, chart_paths)

    log.info("=== Pipeline finished ===")
    return {
        "metadata": metadata,
        "pdf_path": pdf_path,
        "xlsx_path": xlsx_path,
        "issues": all_issues,
        "valid_records": valid_records,
    }