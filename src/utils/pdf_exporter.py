"""
PDF export utility for the Reports module.

Pure rendering helper — takes already-fetched data and writes a PDF file.
Has no knowledge of services/DB, same role SetFormat plays for Qt tables.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def export_table_report(
    file_path: str,
    title: str,
    summary_lines: list[str],
    headers: list[str],
    rows: list[list[str]],
) -> None:
    """
    Writes a single-table PDF report to file_path.

    Args:
        file_path:     Destination path for the generated PDF.
        title:         Report title, rendered as a heading.
        summary_lines: Short summary text lines rendered below the title.
        headers:       Table column headers.
        rows:          Table row data (each row is a list of strings).
    """
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    for line in summary_lines:
        elements.append(Paragraph(line, styles["Normal"]))
    if summary_lines:
        elements.append(Spacer(1, 12))

    table = Table([headers] + rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2196F3")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)

    doc.build(elements)
