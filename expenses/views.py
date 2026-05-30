import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from django.db.models import Sum
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reports.pdf_utils import (
    portrait_style_sheet, portrait_summary_table, portrait_build_table,
    portrait_title_block, portrait_multi_statRow, make_portrait_pdf_response,
    PRIMARY, DARK, BORDER, LIGHT_GRAY, DARK_GRAY, MID_GRAY, BORDER_GRAY,
    WHITE, ACCENT_LINE, PAGE_W_P, PORTRAIT_MARGIN,
)
from .models import Expense
from core.decorators import role_required
from core.pagination import paginate_queryset
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

    qs = qs.order_by("-date", "-id")
    total = qs.aggregate(Sum("amount"))["amount__sum"] or 0
    page_obj = paginate_queryset(request, qs)
    expenses = page_obj

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
        "page_obj": page_obj,
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

    period = None
    if start_str or end_str:
        period = f"{start_str or '…'} to {end_str or '…'}"

    s = portrait_style_sheet()
    elements = []
    portrait_title_block(s, elements, "Expense Report", period=period)

    total_count = qs.count()
    avg_expense = grand_total / total_count if total_count > 0 else 0
    elements.append(portrait_multi_statRow(s, [
        ("Total Expenses", f"₱{grand_total:,.2f}"),
        ("Transactions", str(total_count)),
        ("Average", f"₱{avg_expense:,.2f}"),
    ]))
    elements.append(Spacer(1, 12))

    tbl_width = PAGE_W_P - PORTRAIT_MARGIN * 2

    for key in ["fuel", "toll", "repair", "maintenance", "allowance", "parking", "other"]:
        items = grouped.get(key)
        if not items:
            continue

        section_total = sum(e.amount for e in items)

        section_s = ParagraphStyle("S", parent=s["section"], fontSize=10, textColor=DARK_GRAY, fontName=s["section"].fontName, leading=13)
        sect_total_s = ParagraphStyle("ST", parent=section_s, alignment=TA_RIGHT, textColor=MID_GRAY)
        section_header = Table(
            [[Paragraph(TYPE_LABELS.get(key, key.title()), section_s),
              Paragraph(f"₱{section_total:,.2f}", sect_total_s)]],
            colWidths=[tbl_width * 0.6, tbl_width * 0.4],
        )
        section_header.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, ACCENT_LINE),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("LEFTPADDING", (0, 0), (-1, 0), 1),
            ("RIGHTPADDING", (0, 0), (-1, 0), 1),
        ]))
        elements.append(section_header)

        headers = ["Trip Ref", "Truck", "Type", "Amount", "Date", "Notes"]
        col_widths = [tbl_width * 0.14, tbl_width * 0.13, tbl_width * 0.14, tbl_width * 0.12, tbl_width * 0.13, tbl_width * 0.34]

        rows = []
        for e in items:
            type_display = (
                e.maintenance_record.get_maintenance_type_display()
                if e.expense_type == "maintenance" and e.maintenance_record
                else e.get_expense_type_display()
            )
            trip_ref = e.trip.reference_number if e.trip else "-"
            truck_plate = e.truck.plate_number if e.truck else "-"
            rows.append([
                Paragraph(trip_ref, s["tc"]),
                Paragraph(truck_plate, s["tc"]),
                Paragraph(type_display, s["tcc"]),
                Paragraph(f"₱{e.amount:,.2f}", s["tcr"]),
                Paragraph(e.date.strftime("%b %d, %Y"), s["tcc"]),
                Paragraph(e.notes or "-", s["tc"]),
            ])

        t = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("GRID", (0, 0), (-1, -1), 0.3, ACCENT_LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ]
        header_data = [[Paragraph(h, s["th"]) for h in headers]]
        header_data.extend(rows)
        t = Table(header_data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
        for i in range(1, len(header_data)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), HexColor("#FAF5F0")))
        t.setStyle(TableStyle(style_cmds))
        elements.append(t)
        elements.append(Spacer(1, 8))

    elements.append(HRFlowable(width="100%", thickness=0.5, color=ACCENT_LINE, spaceAfter=4, spaceBefore=4))
    grand_s = ParagraphStyle("GT", parent=s["grand"], fontSize=10, textColor=DARK_GRAY, fontName=s["grand"].fontName, alignment=TA_RIGHT, leading=14, spaceBefore=4)
    elements.append(Paragraph(f"Grand Total: ₱{grand_total:,.2f}", grand_s))

    filename = "expense_report.pdf"
    if expense_type:
        filename = f"expense_report_{expense_type}.pdf"
    return make_portrait_pdf_response(filename, elements, "Expense Report")
