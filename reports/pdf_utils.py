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

# ── Brand colors ───────────────────────────────────────────────
PRIMARY = HexColor("#810B38")
PRIMARY_LIGHT = HexColor("#A31545")
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

# ── Professional portrait theme ──────────────────────────────────
DARK_GRAY = HexColor("#1F2937")
MID_GRAY = HexColor("#4B5563")
BORDER_GRAY = HexColor("#D1D5DB")
LIGHT_BG = HexColor("#F3F4F6")
CREAM_BG = HexColor("#FDF2F4")
ROW_ALT = HexColor("#FAF5F0")
ACCENT_LINE = HexColor("#E8D0D8")
WHITE = HexColor("#FFFFFF")
PAGE_W_P, PAGE_H_P = A4
PORTRAIT_MARGIN = 52

FONT = None
FONT_BOLD = None


def _register_portrait_font():
    global FONT, FONT_BOLD
    if FONT is not None:
        return FONT, FONT_BOLD
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont("ArialH", "arial.ttf"))
        pdfmetrics.registerFont(TTFont("ArialHB", "arialbd.ttf"))
        FONT = "ArialH"
        FONT_BOLD = "ArialHB"
    except Exception:
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            font_path = r"C:\Windows\Fonts\segoeui.ttf"
            bold_path = r"C:\Windows\Fonts\segoeuib.ttf"
            pdfmetrics.registerFont(TTFont("SegoeUI", font_path))
            pdfmetrics.registerFont(TTFont("SegoeUIB", bold_path))
            FONT = "SegoeUI"
            FONT_BOLD = "SegoeUIB"
        except Exception:
            FONT = "Helvetica"
            FONT_BOLD = "Helvetica-Bold"
    return FONT, FONT_BOLD


def _portrait_header_footer(canvas, doc, report_name="Report"):
    canvas.saveState()
    pw, ph = A4

    # Top accent bar — burgundy
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, ph - 8, pw, 8, fill=1, stroke=0)

    # Thin secondary line below accent bar
    canvas.setStrokeColor(ACCENT_LINE)
    canvas.setLineWidth(0.5)
    canvas.line(PORTRAIT_MARGIN, ph - 14, pw - PORTRAIT_MARGIN, ph - 14)

    # Footer separator
    canvas.setStrokeColor(BORDER_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(PORTRAIT_MARGIN, 40, pw - PORTRAIT_MARGIN, 40)

    fnt, fnt_bold = _register_portrait_font()

    # Footer: brand name (left), report name (center), page (right)
    canvas.setFont(fnt, 7)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(PORTRAIT_MARGIN, 28, "Trucking Tracker")
    canvas.setFont(fnt, 6.5)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(pw / 2, 28, report_name)
    canvas.setFont(fnt, 7)
    canvas.setFillColor(MID_GRAY)
    canvas.drawRightString(pw - PORTRAIT_MARGIN, 28, f"Page {doc.page}")

    canvas.restoreState()


def make_portrait_pdf_response(filename, elements, report_name="Report"):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=PORTRAIT_MARGIN + 10, bottomMargin=PORTRAIT_MARGIN,
        leftMargin=PORTRAIT_MARGIN, rightMargin=PORTRAIT_MARGIN,
    )
    frame = Frame(
        PORTRAIT_MARGIN, PORTRAIT_MARGIN,
        PAGE_W_P - PORTRAIT_MARGIN * 2, PAGE_H_P - PORTRAIT_MARGIN * 2 - 10,
        id="normal",
    )
    cb = lambda c, d: _portrait_header_footer(c, d, report_name)
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=cb)])
    doc.build(elements)
    buf.seek(0)
    resp = HttpResponse(buf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def portrait_style_sheet():
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    f, fb = _register_portrait_font()
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("T", parent=styles["Title"], fontSize=18, textColor=DARK_GRAY, fontName=fb, spaceAfter=2, leading=22),
        "meta": ParagraphStyle("M", parent=styles["Normal"], fontSize=8, textColor=MID_GRAY, fontName=f, alignment=TA_RIGHT, leading=10, spaceAfter=14),
        "section": ParagraphStyle("S", parent=styles["Normal"], fontSize=10, textColor=DARK_GRAY, fontName=fb, leading=13),
        "section_total": ParagraphStyle("ST", parent=styles["Normal"], fontSize=10, textColor=MID_GRAY, fontName=fb, alignment=TA_RIGHT, leading=13),
        "grand": ParagraphStyle("GT", parent=styles["Normal"], fontSize=10, textColor=DARK_GRAY, fontName=fb, alignment=TA_RIGHT, leading=14, spaceBefore=4),
        "th": ParagraphStyle("TH", parent=styles["Normal"], fontSize=7.5, textColor=WHITE, fontName=fb, alignment=TA_CENTER, leading=10),
        "tc": ParagraphStyle("TC", parent=styles["Normal"], fontSize=7.5, textColor=DARK_GRAY, fontName=f, leading=10),
        "tcc": ParagraphStyle("TCC", parent=styles["Normal"], fontSize=7.5, textColor=DARK_GRAY, fontName=f, alignment=TA_CENTER, leading=10),
        "tcr": ParagraphStyle("TCR", parent=styles["Normal"], fontSize=7.5, textColor=DARK_GRAY, fontName=f, alignment=TA_RIGHT, leading=10),
        "stat_label": ParagraphStyle("SL", parent=styles["Normal"], fontSize=8, textColor=MID_GRAY, fontName=f, leading=10),
        "stat_value": ParagraphStyle("SV", parent=styles["Normal"], fontSize=14, textColor=DARK_GRAY, fontName=fb, alignment=TA_RIGHT, leading=17),
        "stat_value_accent": ParagraphStyle("SVA", parent=styles["Normal"], fontSize=14, textColor=PRIMARY, fontName=fb, alignment=TA_RIGHT, leading=17),
        "stat_label_accent": ParagraphStyle("SLA", parent=styles["Normal"], fontSize=8, textColor=PRIMARY, fontName=fb, leading=10),
        "kpi_value": ParagraphStyle("KPIV", parent=styles["Normal"], fontSize=16, textColor=DARK_GRAY, fontName=fb, alignment=TA_CENTER, leading=20),
        "kpi_label": ParagraphStyle("KPIL", parent=styles["Normal"], fontSize=7.5, textColor=MID_GRAY, fontName=f, alignment=TA_CENTER, leading=10),
    }


def php(value):
    """Format a number as Philippine Peso currency (P 1,234.56)."""
    if isinstance(value, (int, float)):
        return f"P {value:,.2f}"
    return str(value)


def portrait_summary_table(s, value, label="Total"):
    data = [[Paragraph(label, s["stat_label_accent"]), Paragraph(php(value), s["stat_value_accent"])]]
    tw = PAGE_W_P - PORTRAIT_MARGIN * 2
    tbl = Table(data, colWidths=[tw * 0.3, tw * 0.7])
    tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, ACCENT_LINE),
        ("LINEAFTER", (0, 0), (0, -1), 2, PRIMARY),
        ("BACKGROUND", (0, 0), (-1, -1), CREAM_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl


def portrait_multi_statRow(s, stats, bg_color=None):
    """Create a row of stat boxes. stats = [(label, value), ...]"""
    tw = PAGE_W_P - PORTRAIT_MARGIN * 2
    n = len(stats)
    col_w = tw / n

    label_row = []
    value_row = []
    for label, value in stats:
        label_row.append(Paragraph(label, s["kpi_label"]))
        display = php(value) if isinstance(value, (int, float)) else str(value)
        value_row.append(Paragraph(display, s["kpi_value"]))

    data = [label_row, value_row]
    bg = bg_color or LIGHT_BG
    tbl = Table(data, colWidths=[col_w] * n)
    cmds = [
        ("BOX", (0, 0), (-1, -1), 0.5, ACCENT_LINE),
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]
    # Vertical dividers between columns
    for i in range(1, n):
        cmds.append(("LINEAFTER", (i - 1, 0), (i - 1, -1), 0.3, ACCENT_LINE))
    tbl.setStyle(TableStyle(cmds))
    return tbl


def portrait_build_table(s, headers, rows, col_widths=None):
    data = [[Paragraph(h, s["th"]) for h in headers]]
    data.extend(rows)
    tw = PAGE_W_P - PORTRAIT_MARGIN * 2
    cw = col_widths or [tw / len(headers)] * len(headers)
    t = Table(data, colWidths=cw, repeatRows=1, hAlign="LEFT")
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.3, ACCENT_LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(cmds))
    return t


def portrait_title_block(s, elements, title, period=None):
    from datetime import datetime
    elements.append(Paragraph(title, s["title"]))
    parts = []
    if period:
        parts.append(f"Period: {period}")
    parts.append(f"Generated {datetime.now().strftime('%B %d, %Y')}")
    elements.append(Paragraph(" • ".join(parts), s["meta"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=10, spaceBefore=0))


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
