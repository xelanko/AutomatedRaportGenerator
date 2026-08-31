"""
PDF export using ReportLab. Builds a title page, summary table,
embedded charts, and a validation-issues appendix.
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
import logger_setup
from models import ReportMetadata

log = logger_setup.get_logger(__name__)


def build_pdf_report(
    output_path: Path,
    metadata: ReportMetadata,
    records,
    narrative_text: str,
    chart_paths: list[Path],
    validation_issues: list = None,
) -> Path:
    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                             topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=22)
    story = []

    # --- Title page ---
    story.append(Paragraph(metadata.title, title_style))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        f"Period: {metadata.period_start} to {metadata.period_end}<br/>"
        f"Generated: {metadata.generated_at.strftime('%Y-%m-%d %H:%M')}<br/>"
        f"Total records: {metadata.total_records}<br/>"
        f"Validation: {metadata.validation_error_count} errors, "
        f"{metadata.validation_warning_count} warnings",
        styles["Normal"]))
    story.append(Spacer(1, 1 * cm))

    # --- Narrative summary ---
    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(Paragraph(narrative_text, styles["Normal"]))
    story.append(Spacer(1, 1 * cm))

    # --- Data table (top rows) ---
    story.append(Paragraph("Sample Data", styles["Heading2"]))
    table_data = [["Date", "Region", "Category", "Revenue", "Qty"]]
    for r in records[:20]:
        table_data.append([str(r.record_date), r.region, r.category,
                            f"{r.revenue:,.2f}", str(r.quantity)])
    table = Table(table_data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4C72B0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F0F0")]),
    ]))
    story.append(table)
    story.append(PageBreak())

    # --- Charts ---
    story.append(Paragraph("Charts", styles["Heading2"]))
    for chart_path in chart_paths:
        story.append(Image(str(chart_path), width=14 * cm, height=9 * cm))
        story.append(Spacer(1, 0.5 * cm))

    # --- Validation appendix ---
    if validation_issues:
        story.append(PageBreak())
        story.append(Paragraph("Validation Issues", styles["Heading2"]))
        issue_data = [["Level", "Field", "Record ID", "Message"]]
        for issue in validation_issues:
            issue_data.append([issue.level, issue.field or "-",
                                issue.record_id or "-", issue.message])
        issue_table = Table(issue_data, hAlign="LEFT", colWidths=[2 * cm, 2.5 * cm, 3 * cm, 8 * cm])
        issue_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C44E52")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(issue_table)

    doc.build(story)
    log.info(f"PDF report written to {output_path}")
    return output_path