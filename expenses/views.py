import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from django.db.models import Sum
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable, SimpleDocTemplate
from reports.pdf_utils import PRIMARY, DARK, BORDER, LIGHT_GRAY
from .models import Expense
from core.decorators import role_required
from trips.models import Trip
from trucks.models import Truck

logger = logging.getLogger(__name__)


@login_required
@role_required("admin", "dispatcher")
def expense_list_view(request):
    qs = Expense.objects.all().select_related("trip", "truck", "maintenance_record")

    expense_type = request.GET.get("expense_type")
    if expense_type:
        qs = qs.filter(expense_type=expense_type)

    start = request.GET.get("start")
    end = request.GET.get("end")
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)

    expenses = qs

    total = expenses.aggregate(Sum("amount"))["amount__sum"] or 0

    grouped = {}
    for exp in expenses:
        grouped.setdefault(exp.expense_type, []).append(exp)

    TYPE_LABELS = {
        "fuel": "Fuel", "toll": "Toll", "repair": "Repair",
        "maintenance": "Maintenance", "allowance": "Driver Allowance",
        "parking": "Parking", "other": "Other",
    }

    type_sections = []
    for key in ["fuel", "toll", "repair", "maintenance", "allowance", "parking", "other"]:
        items = grouped.get(key)
        if items:
            section_total = sum(item.amount for item in items)
            type_sections.append({
                "key": key,
                "label": TYPE_LABELS.get(key, key.title()),
                "items": items,
                "total": section_total,
            })

    return render(request, "expenses/expense_list.html", {
        "expenses": expenses,
        "type_sections": type_sections,
        "total": total,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def expense_create_view(request):
    if request.method == "POST":
        Expense.objects.create(
            trip_id=request.POST.get("trip") or None,
            truck_id=request.POST.get("truck") or None,
            expense_type=request.POST.get("expense_type"),
            amount=request.POST.get("amount"),
            date=request.POST.get("date"),
            receipt=request.FILES.get("receipt"),
            notes=request.POST.get("notes"),
        )
        messages.success(request, "Expense recorded.")
        return redirect("expense_list")
    trips = Trip.objects.all()
    trucks = Truck.objects.all()
    return render(request, "expenses/expense_form.html", {"trips": trips, "trucks": trucks})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def expense_edit_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.trip_id = request.POST.get("trip") or None
        expense.truck_id = request.POST.get("truck") or None
        expense.expense_type = request.POST.get("expense_type")
        expense.amount = request.POST.get("amount")
        expense.date = request.POST.get("date")
        if request.FILES.get("receipt"):
            expense.receipt = request.FILES["receipt"]
        expense.notes = request.POST.get("notes")
        expense.save()
        messages.success(request, "Expense updated.")
        return redirect("expense_list")
    trips = Trip.objects.all()
    trucks = Truck.objects.all()
    return render(request, "expenses/expense_form.html", {
        "expense": expense, "trips": trips, "trucks": trucks
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def expense_delete_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Expense deleted.")
        return redirect("expense_list")
    return render(request, "expenses/expense_confirm_delete.html", {"expense": expense})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def expense_modal_create(request):
    trips = Trip.objects.all()
    trucks = Truck.objects.all()
    if request.method == "POST":
        try:
            Expense.objects.create(
                trip_id=request.POST.get("trip") or None,
                truck_id=request.POST.get("truck") or None,
                expense_type=request.POST.get("expense_type"),
                amount=request.POST.get("amount"),
                date=request.POST.get("date"),
                receipt=request.FILES.get("receipt"),
                notes=request.POST.get("notes"),
            )
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("expense_list")
            return response
        except Exception as e:
            logger.exception("Error creating expense")
            return render(request, "expenses/_form.html", {
                "form_expense": None, "trips": trips, "trucks": trucks,
                "action_url": reverse("expense_modal_create"), "error": "An unexpected error occurred. Please check your input.",
            })
    return render(request, "expenses/_form.html", {
        "form_expense": None, "trips": trips, "trucks": trucks,
        "action_url": reverse("expense_modal_create"),
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def expense_modal_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    trips = Trip.objects.all()
    trucks = Truck.objects.all()
    if request.method == "POST":
        try:
            expense.trip_id = request.POST.get("trip") or None
            expense.truck_id = request.POST.get("truck") or None
            expense.expense_type = request.POST.get("expense_type")
            expense.amount = request.POST.get("amount")
            expense.date = request.POST.get("date")
            if request.FILES.get("receipt"):
                expense.receipt = request.FILES["receipt"]
            expense.notes = request.POST.get("notes")
            expense.save()
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("expense_list")
            return response
        except Exception as e:
            logger.exception("Error editing expense %s", pk)
            return render(request, "expenses/_form.html", {
                "form_expense": expense, "trips": trips, "trucks": trucks,
                "action_url": reverse("expense_modal_edit", args=[pk]), "error": "An unexpected error occurred. Please check your input.",
            })
    return render(request, "expenses/_form.html", {
        "form_expense": expense, "trips": trips, "trucks": trucks,
        "action_url": reverse("expense_modal_edit", args=[pk]),
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def expense_modal_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        response = HttpResponse()
        response["HX-Trigger"] = "closeModal"
        response["HX-Redirect"] = reverse("expense_list")
        return response
    return render(request, "expenses/_delete.html", {
        "object": expense, "action_url": reverse("expense_modal_delete", args=[pk]),
    })


@login_required
@role_required("admin", "dispatcher")
def expense_list_pdf(request):
    from datetime import datetime
    from reportlab.platypus.frames import Frame
    from reportlab.platypus.doctemplate import PageTemplate
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    FONT = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"
    try:
        pdfmetrics.registerFont(TTFont("ArialH", "arial.ttf"))
        pdfmetrics.registerFont(TTFont("ArialHB", "arialbd.ttf"))
        FONT = "ArialH"
        FONT_BOLD = "ArialHB"
    except Exception:
        try:
            font_path = r"C:\Windows\Fonts\segoeui.ttf"
            bold_path = r"C:\Windows\Fonts\segoeuib.ttf"
            pdfmetrics.registerFont(TTFont("SegoeUI", font_path))
            pdfmetrics.registerFont(TTFont("SegoeUIB", bold_path))
            FONT = "SegoeUI"
            FONT_BOLD = "SegoeUIB"
        except Exception:
            pass

    qs = Expense.objects.all().select_related("trip", "truck", "maintenance_record")

    expense_type = request.GET.get("expense_type")
    if expense_type:
        qs = qs.filter(expense_type=expense_type)

    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    if start_str:
        qs = qs.filter(date__gte=start_str)
    if end_str:
        qs = qs.filter(date__lte=end_str)

    TYPE_LABELS = {
        "fuel": "Fuel", "toll": "Toll", "repair": "Repair",
        "maintenance": "Maintenance", "allowance": "Driver Allowance",
        "parking": "Parking", "other": "Other",
    }

    grouped = {}
    for exp in qs:
        grouped.setdefault(exp.expense_type, []).append(exp)

    grand_total = sum(e.amount for e in qs)

    date_parts = []
    if start_str:
        date_parts.append(start_str)
    if end_str:
        date_parts.append(end_str)

    DARK_GRAY = HexColor("#1F2937")
    MID_GRAY = HexColor("#4B5563")
    LIGHT_GRAY2 = HexColor("#F3F4F6")
    WHITE = HexColor("#FFFFFF")
    PAGE_W, PAGE_H = A4
    MARGIN = 52

    now = datetime.now()
    gen_date = now.strftime("%B %d, %Y")

    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("T", parent=styles["Title"], fontSize=18, textColor=DARK_GRAY, fontName=FONT_BOLD, spaceAfter=2, leading=22)
    meta_s = ParagraphStyle("M", parent=styles["Normal"], fontSize=8, textColor=MID_GRAY, fontName=FONT, alignment=TA_RIGHT, leading=10, spaceAfter=14)
    section_s = ParagraphStyle("S", parent=styles["Normal"], fontSize=10, textColor=DARK_GRAY, fontName=FONT_BOLD, leading=13)
    sect_total_s = ParagraphStyle("ST", parent=section_s, alignment=TA_RIGHT, textColor=MID_GRAY)
    grand_s = ParagraphStyle("GT", parent=styles["Normal"], fontSize=10, textColor=DARK_GRAY, fontName=FONT_BOLD, alignment=TA_RIGHT, leading=14, spaceBefore=4)
    th_s = ParagraphStyle("TH", parent=styles["Normal"], fontSize=7.5, textColor=WHITE, fontName=FONT_BOLD, alignment=TA_CENTER, leading=10)
    tc_s = ParagraphStyle("TC", parent=styles["Normal"], fontSize=7.5, textColor=DARK_GRAY, fontName=FONT, leading=10)
    tcc_s = ParagraphStyle("TCC", parent=tc_s, alignment=TA_CENTER)
    tcr_s = ParagraphStyle("TCR", parent=tc_s, alignment=TA_RIGHT)

    def header_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(HexColor("#D1D5DB"))
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, 36, PAGE_W - MARGIN, 36)
        canvas.setFont(FONT, 7)
        canvas.setFillColor(MID_GRAY)
        canvas.drawString(MARGIN, 24, "Trucking Tracker — Expense Report")
        canvas.drawRightString(PAGE_W - MARGIN, 24, f"Page {doc.page}")
        canvas.restoreState()

    elements = []

    # --- Letterhead / Title area ---
    elements.append(Paragraph("Expense Report", title_s))

    header_parts = []
    if start_str or end_str:
        period = f"{start_str or '…'} to {end_str or '…'}"
        header_parts.append(f"Period: {period}")
    header_parts.append(f"Generated {gen_date}")
    elements.append(Paragraph(" &bull; ".join(header_parts), meta_s))

    elements.append(HRFlowable(width="100%", thickness=1.5, color=DARK_GRAY, spaceAfter=10, spaceBefore=0))

    # --- Summary row (Total figure) ---
    summary_data = [[
        Paragraph("Total Expenses", ParagraphStyle("SL", parent=styles["Normal"], fontSize=8, textColor=MID_GRAY, fontName=FONT, leading=10)),
        Paragraph(f"₱{grand_total:,.2f}", ParagraphStyle("SV", parent=styles["Normal"], fontSize=14, textColor=DARK_GRAY, fontName=FONT_BOLD, alignment=TA_RIGHT, leading=17)),
    ]]
    summary_tbl = Table(summary_data, colWidths=[PAGE_W * 0.3, PAGE_W * 0.7 - MARGIN * 2])
    summary_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#D1D5DB")),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY2),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(summary_tbl)
    elements.append(Spacer(1, 12))

    # --- Section tables ---
    for key in ["fuel", "toll", "repair", "maintenance", "allowance", "parking", "other"]:
        items = grouped.get(key)
        if not items:
            continue

        section_total = sum(e.amount for e in items)
        tbl_width = PAGE_W - MARGIN * 2

        section_header = Table(
            [[Paragraph(f"{TYPE_LABELS.get(key, key.title())}", section_s),
              Paragraph(f"₱{section_total:,.2f}", sect_total_s)]],
            colWidths=[tbl_width * 0.6, tbl_width * 0.4],
        )
        section_header.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, HexColor("#D1D5DB")),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("LEFTPADDING", (0, 0), (-1, 0), 1),
            ("RIGHTPADDING", (0, 0), (-1, 0), 1),
        ]))
        elements.append(section_header)

        headers = ["Trip Ref", "Truck", "Type", "Amount", "Date", "Notes"]
        col_widths = [tbl_width * 0.14, tbl_width * 0.13, tbl_width * 0.14, tbl_width * 0.12, tbl_width * 0.13, tbl_width * 0.34]

        data = [[Paragraph(h, th_s) for h in headers]]
        for e in items:
            type_display = (
                e.maintenance_record.get_maintenance_type_display()
                if e.expense_type == "maintenance" and e.maintenance_record
                else e.get_expense_type_display()
            )
            trip_ref = e.trip.reference_number if e.trip else "-"
            truck_plate = e.truck.plate_number if e.truck else "-"
            data.append([
                Paragraph(trip_ref, tc_s),
                Paragraph(truck_plate, tc_s),
                Paragraph(type_display, tcc_s),
                Paragraph(f"₱{e.amount:,.2f}", tcr_s),
                Paragraph(e.date.strftime("%b %d, %Y"), tcc_s),
                Paragraph(e.notes or "-", tc_s),
            ])

        t = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), DARK_GRAY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("GRID", (0, 0), (-1, -1), 0.3, HexColor("#D1D5DB")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ]
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), HexColor("#F9FAFB")))
        t.setStyle(TableStyle(style_cmds))
        elements.append(t)
        elements.append(Spacer(1, 8))

    # --- Grand total ---
    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#D1D5DB"), spaceAfter=4, spaceBefore=4))
    elements.append(Paragraph(f"Grand Total: ₱{grand_total:,.2f}", grand_s))

    # --- Build PDF ---
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=MARGIN, bottomMargin=MARGIN,
        leftMargin=MARGIN, rightMargin=MARGIN,
    )
    frame = Frame(MARGIN, MARGIN, PAGE_W - MARGIN * 2, PAGE_H - MARGIN * 2, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=header_footer)])
    doc.build(elements)
    buf.seek(0)

    filename = "expense_report.pdf"
    if expense_type:
        filename = f"expense_report_{expense_type}.pdf"
    resp = HttpResponse(buf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp
