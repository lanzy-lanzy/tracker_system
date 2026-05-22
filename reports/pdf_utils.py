from io import BytesIO
from datetime import datetime
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, HRFlowable
)
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate

PRIMARY = HexColor("#810B38")
DARK = HexColor("#541A1A")
CREAM = HexColor("#F1E2D1")
BORDER = HexColor("#DCC3AA")
WHITE = HexColor("#FFFFFF")
GRAY = HexColor("#6B7280")
LIGHT_GRAY = HexColor("#F3F4F6")
GREEN = HexColor("#16A34A")
RED = HexColor("#DC2626")

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "ReportTitle", parent=styles["Title"],
    fontSize=18, textColor=DARK, spaceAfter=2, alignment=TA_LEFT,
    fontName="Helvetica-Bold",
    leading=22,
)

subtitle_style = ParagraphStyle(
    "ReportSubtitle", parent=styles["Normal"],
    fontSize=9, textColor=GRAY, spaceAfter=14, alignment=TA_LEFT,
    fontName="Helvetica",
    leading=12,
)

table_header_style = ParagraphStyle(
    "TableHeader", parent=styles["Normal"],
    fontSize=7.5, textColor=WHITE, alignment=TA_CENTER,
    fontName="Helvetica-Bold",
    leading=10,
)

table_cell_style = ParagraphStyle(
    "TableCell", parent=styles["Normal"],
    fontSize=7.5, textColor=HexColor("#374151"), alignment=TA_LEFT,
    fontName="Helvetica",
    leading=11,
)

table_cell_center = ParagraphStyle(
    "TableCellCenter", parent=table_cell_style,
    alignment=TA_CENTER,
)

table_cell_right = ParagraphStyle(
    "TableCellRight", parent=table_cell_style,
    alignment=TA_RIGHT,
)

stat_value_style = ParagraphStyle(
    "StatValue", parent=styles["Normal"],
    fontSize=14, textColor=PRIMARY, fontName="Helvetica-Bold",
)

stat_label_style = ParagraphStyle(
    "StatLabel", parent=styles["Normal"],
    fontSize=8, textColor=DARK, fontName="Helvetica-Bold",
    leading=10,
)

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(20, PAGE_HEIGHT - 18, PAGE_WIDTH - 20, PAGE_HEIGHT - 18)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.3)
    canvas.line(20, 16, PAGE_WIDTH - 20, 16)
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(20, 4, "Trucking Tracker — Fleet Management System")
    now = datetime.now().strftime("%b %d, %Y %I:%M %p")
    canvas.drawString(PAGE_WIDTH // 2 - 50, 4, f"Generated: {now}")
    canvas.drawRightString(PAGE_WIDTH - 20, 4, f"Page {doc.page}")
    canvas.restoreState()


def _build_table(headers, rows, col_widths=None):
    header_row = [Paragraph(h, table_header_style) for h in headers]
    data = [header_row]
    for row in rows:
        data.append(row)

    t = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
    ]

    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY))

    t.setStyle(TableStyle(style_cmds))
    return t


def _stat_block(label, value, color=PRIMARY):
    return Table(
        [
            [Paragraph(label, stat_label_style)],
            [Paragraph(f"P{value:,.2f}", ParagraphStyle("sv", parent=stat_value_style, textColor=color))],
        ],
        colWidths=[120],
        hAlign="LEFT",
    )


def make_pdf_response(filename, elements):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        topMargin=26, bottomMargin=22,
        leftMargin=20, rightMargin=20,
    )
    frame = Frame(
        20, 22, PAGE_WIDTH - 40, PAGE_HEIGHT - 48,
        id="normal",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=_header_footer)])
    doc.build(elements)
    buf.seek(0)
    resp = HttpResponse(buf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def add_title(elements, title, subtitle=None, date_range=None):
    elements.append(Paragraph(title, title_style))
    parts = []
    if subtitle:
        parts.append(subtitle)
    if date_range:
        parts.append(f"Period: {date_range}")
    if parts:
        elements.append(Paragraph(" | ".join(parts), subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=10, spaceBefore=0))
