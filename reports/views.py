from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from core.utils import is_driver
from core.cache_utils import get_or_set_cache
from trips.models import Trip
from trucks.models import Truck
from drivers.models import Driver
from maintenance.models import Maintenance
from expenses.models import Expense
from payments.models import Payment
from clients.models import Client

from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from .pdf_utils import (
    portrait_style_sheet, portrait_summary_table, portrait_build_table,
    portrait_title_block, make_portrait_pdf_response, portrait_multi_statRow,
    DARK_GRAY, MID_GRAY, BORDER_GRAY, WHITE, PRIMARY, GREEN, RED,
    PAGE_W_P, PORTRAIT_MARGIN, ACCENT_LINE, LIGHT_BG,
)


def get_date_range(request):
    start = request.GET.get("start_date")
    end = request.GET.get("end_date")
    if not start:
        start = timezone.now().replace(day=1).date()
    if not end:
        end = timezone.now().date()
    return start, end


def _fmt_date(d):
    return d.strftime("%b %d, %Y") if hasattr(d, "strftime") else str(d)


def _range_str(start, end):
    return f"{_fmt_date(start)} - {_fmt_date(end)}"


@login_required
def report_dashboard_view(request):
    if is_driver(request.user):
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    return render(request, "reports/report_dashboard.html")


@login_required
def daily_trip_report(request):
    start, end = get_date_range(request)
    trips = Trip.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
    status = request.GET.get("status", "")
    if status:
        trips = trips.filter(status=status)
    return render(request, "reports/daily_trip_report.html", {
        "trips": trips, "start": start, "end": end, "status": status
    })


@login_required
def monthly_trip_report(request):
    start, end = get_date_range(request)
    trips = Trip.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
    total_trips = trips.count()
    completed_trips = trips.filter(status="delivered").count()
    cancelled_trips = trips.filter(status="cancelled").count()
    in_transit_trips = trips.filter(status="in_transit").count()
    return render(request, "reports/monthly_trip_report.html", {
        "trips": trips, "start": start, "end": end,
        "total_trips": total_trips, "completed_trips": completed_trips,
        "cancelled_trips": cancelled_trips, "in_transit_trips": in_transit_trips,
    })


@login_required
def truck_utilization_report(request):
    trucks = get_or_set_cache("reports:utilization:trucks", lambda: list(
        Truck.objects.annotate(
            total_trips=Count("trips"),
            completed_trips=Count("trips", filter=Q(trips__status="delivered")),
        )
    ))
    return render(request, "reports/truck_utilization.html", {"trucks": trucks})


@login_required
def driver_performance_report(request):
    drivers = get_or_set_cache("reports:performance:drivers", lambda: list(
        Driver.objects.annotate(
            total_trips=Count("trips"),
            completed_trips=Count("trips", filter=Q(trips__status="delivered")),
        )
    ))
    for d in drivers:
        d.cancelled_trips = d.total_trips - d.completed_trips
        d.completion_rate = (d.completed_trips / d.total_trips * 100) if d.total_trips > 0 else 0
    return render(request, "reports/driver_performance.html", {"drivers": drivers})


@login_required
def maintenance_report(request):
    start, end = get_date_range(request)
    records = Maintenance.objects.filter(service_date__gte=start, service_date__lte=end)
    total_cost = records.aggregate(Sum("cost"))["cost__sum"] or 0
    return render(request, "reports/maintenance_report.html", {
        "maintenance_records": records, "start": start, "end": end,
        "total_cost": total_cost,
    })


@login_required
def expense_report(request):
    start, end = get_date_range(request)
    expenses = Expense.objects.filter(date__gte=start, date__lte=end)
    expense_type = request.GET.get("expense_type", "")
    if expense_type:
        expenses = expenses.filter(expense_type=expense_type)
    total = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
    return render(request, "reports/expense_report.html", {
        "expenses": expenses, "start": start, "end": end,
        "expense_type": expense_type, "total": total
    })


@login_required
def payment_report(request):
    start, end = get_date_range(request)
    payments = Payment.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
    status = request.GET.get("status", "")
    if status:
        payments = payments.filter(payment_status=status)
    total_collected = payments.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    total_due = payments.aggregate(Sum("amount_due"))["amount_due__sum"] or 0
    return render(request, "reports/payment_report.html", {
        "payments": payments, "start": start, "end": end,
        "status": status, "total_collected": total_collected, "total_due": total_due
    })


@login_required
def profit_loss_report(request):
    start, end = get_date_range(request)
    revenue = Payment.objects.filter(
        payment_date__gte=start, payment_date__lte=end, payment_status="paid"
    ).aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    expenses_total = Expense.objects.filter(
        date__gte=start, date__lte=end
    ).aggregate(Sum("amount"))["amount__sum"] or 0
    profit = revenue - expenses_total
    return render(request, "reports/profit_loss.html", {
        "revenue": revenue, "expenses": expenses_total,
        "profit": profit, "start": start, "end": end
    })


# ── PDF views (professional portrait theme) ─────────────────────

def _pdf_rows_for_trips(s, trips):
    rows = []
    for t in trips:
        rows.append([
            Paragraph(t.reference_number or "-", s["tc"]),
            Paragraph(t.client.client_name if t.client else "-", s["tc"]),
            Paragraph(t.assigned_driver.full_name if t.assigned_driver else "-", s["tc"]),
            Paragraph(t.pickup_location or "-", s["tc"]),
            Paragraph(t.dropoff_location or "-", s["tc"]),
            Paragraph(t.get_status_display(), s["tcc"]),
            Paragraph(_fmt_date(t.scheduled_delivery) if t.scheduled_delivery else "-", s["tcc"]),
        ])
    return rows


@login_required
def daily_trip_pdf(request):
    start, end = get_date_range(request)
    trips = Trip.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
    status_filter = request.GET.get("status", "")
    if status_filter:
        trips = trips.filter(status=status_filter)
    s = portrait_style_sheet()
    elements = []
    portrait_title_block(s, elements, "Daily Trip Report", period=_range_str(start, end))

    total = trips.count()
    completed = trips.filter(status="delivered").count()
    in_transit = trips.filter(status="in_transit").count()
    elements.append(portrait_multi_statRow(s, [
        ("Total Trips", str(total)),
        ("Completed", str(completed)),
        ("In Transit", str(in_transit)),
    ]))
    elements.append(Spacer(1, 10))

    headers = ["Ref#", "Client", "Driver", "Pickup", "Dropoff", "Status", "Sched. Delivery"]
    rows = _pdf_rows_for_trips(s, trips)
    if rows:
        elements.append(portrait_build_table(s, headers, rows))
    return make_portrait_pdf_response("daily_trip_report.pdf", elements, "Daily Trip Report")


@login_required
def monthly_trip_pdf(request):
    start, end = get_date_range(request)
    trips = Trip.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
    total = trips.count()
    completed = trips.filter(status="delivered").count()
    cancelled = trips.filter(status="cancelled").count()
    in_transit = trips.filter(status="in_transit").count()
    s = portrait_style_sheet()
    elements = []
    portrait_title_block(s, elements, "Monthly Trip Report", period=_range_str(start, end))

    elements.append(portrait_multi_statRow(s, [
        ("Total Trips", str(total)),
        ("Completed", str(completed)),
        ("In Transit", str(in_transit)),
        ("Cancelled", str(cancelled)),
    ]))
    elements.append(Spacer(1, 10))

    headers = ["Ref#", "Client", "Driver", "Pickup", "Dropoff", "Status", "Sched. Delivery"]
    rows = _pdf_rows_for_trips(s, trips)
    if rows:
        elements.append(portrait_build_table(s, headers, rows))
    return make_portrait_pdf_response("monthly_trip_report.pdf", elements, "Monthly Trip Report")


@login_required
def truck_utilization_pdf(request):
    trucks = Truck.objects.annotate(
        total_trips=Count("trips"),
        completed_trips=Count("trips", filter=Q(trips__status="delivered")),
    )
    s = portrait_style_sheet()
    elements = []
    portrait_title_block(s, elements, "Truck Utilization Report")

    total_trucks = trucks.count()
    active_trucks = trucks.filter(status="active").count()
    avg_rate = 0
    if total_trucks > 0:
        rates = [((t.completed_trips / t.total_trips * 100) if t.total_trips > 0 else 0) for t in trucks]
        avg_rate = sum(rates) / len(rates)
    elements.append(portrait_multi_statRow(s, [
        ("Total Trucks", str(total_trucks)),
        ("Active", str(active_trucks)),
        ("Avg. Completion", f"{avg_rate:.1f}%"),
    ]))
    elements.append(Spacer(1, 10))

    headers = ["Plate #", "Type", "Total Trips", "Completed", "Rate", "Status"]
    rows = []
    for truck in trucks:
        rate = f"{(truck.completed_trips / truck.total_trips * 100):.1f}%" if truck.total_trips > 0 else "-"
        rows.append([
            Paragraph(truck.plate_number, s["tc"]),
            Paragraph(truck.get_truck_type_display() or "-", s["tc"]),
            Paragraph(str(truck.total_trips), s["tcc"]),
            Paragraph(str(truck.completed_trips), s["tcc"]),
            Paragraph(rate, s["tcc"]),
            Paragraph(truck.get_status_display(), s["tcc"]),
        ])
    elements.append(portrait_build_table(s, headers, rows))
    return make_portrait_pdf_response("truck_utilization.pdf", elements, "Truck Utilization")


@login_required
def driver_performance_pdf(request):
    drivers = Driver.objects.annotate(
        total_trips=Count("trips"),
        completed_trips=Count("trips", filter=Q(trips__status="delivered")),
    )
    s = portrait_style_sheet()
    elements = []
    portrait_title_block(s, elements, "Driver Performance Report")

    total_drivers = drivers.count()
    avg_rate = 0
    if total_drivers > 0:
        rates = [((d.completed_trips / d.total_trips * 100) if d.total_trips > 0 else 0) for d in drivers]
        avg_rate = sum(rates) / len(rates)
    elements.append(portrait_multi_statRow(s, [
        ("Total Drivers", str(total_drivers)),
        ("Avg. Completion", f"{avg_rate:.1f}%"),
    ]))
    elements.append(Spacer(1, 10))

    GREEN_RATE = HexColor("#16A34A")
    YELLOW_RATE = HexColor("#D97706")
    RED_RATE = HexColor("#DC2626")

    headers = ["Driver", "Total Trips", "Completed", "Cancelled", "Rate"]
    rows = []
    for d in drivers:
        total = d.total_trips
        completed = d.completed_trips
        cancelled = total - completed if total >= completed else 0
        rate_val = (completed / total * 100) if total > 0 else 0
        rate_str = f"{rate_val:.1f}%" if total > 0 else "-"
        if rate_val >= 80:
            rate_color = GREEN_RATE
        elif rate_val >= 50:
            rate_color = YELLOW_RATE
        else:
            rate_color = RED_RATE
        rate_style = ParagraphStyle("RC", parent=s["tcc"], textColor=rate_color, fontName=s["tcc"].fontName)
        rows.append([
            Paragraph(d.full_name, s["tc"]),
            Paragraph(str(total), s["tcc"]),
            Paragraph(str(completed), s["tcc"]),
            Paragraph(str(cancelled), s["tcc"]),
            Paragraph(rate_str, rate_style),
        ])
    elements.append(portrait_build_table(s, headers, rows))
    return make_portrait_pdf_response("driver_performance.pdf", elements, "Driver Performance")


@login_required
def maintenance_pdf(request):
    start, end = get_date_range(request)
    records = Maintenance.objects.filter(service_date__gte=start, service_date__lte=end)
    total_cost = records.aggregate(Sum("cost"))["cost__sum"] or 0
    s = portrait_style_sheet()
    elements = []
    portrait_title_block(s, elements, "Maintenance Report", period=_range_str(start, end))

    total_records = records.count()
    completed = records.filter(status="completed").count()
    pending = records.filter(status="pending").count()
    elements.append(portrait_multi_statRow(s, [
        ("Total Records", str(total_records)),
        ("Completed", str(completed)),
        ("Pending", str(pending)),
        ("Total Cost", f"₱{total_cost:,.2f}"),
    ]))
    elements.append(Spacer(1, 10))

    headers = ["Truck", "Type", "Service Date", "Cost", "Status"]
    rows = []
    for r in records:
        rows.append([
            Paragraph(r.truck.plate_number, s["tc"]),
            Paragraph(r.get_maintenance_type_display(), s["tc"]),
            Paragraph(_fmt_date(r.service_date), s["tcc"]),
            Paragraph(f"₱{r.cost:,.2f}" if r.cost else "-", s["tcr"]),
            Paragraph(r.get_status_display(), s["tcc"]),
        ])
    elements.append(portrait_build_table(s, headers, rows))
    return make_portrait_pdf_response("maintenance_report.pdf", elements, "Maintenance Report")


@login_required
def expense_pdf(request):
    start, end = get_date_range(request)
    expenses = Expense.objects.filter(date__gte=start, date__lte=end)
    expense_type = request.GET.get("expense_type", "")
    if expense_type:
        expenses = expenses.filter(expense_type=expense_type)
    total = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
    s = portrait_style_sheet()
    elements = []
    portrait_title_block(s, elements, "Expense Report", period=_range_str(start, end))

    total_count = expenses.count()
    avg_expense = total / total_count if total_count > 0 else 0
    elements.append(portrait_multi_statRow(s, [
        ("Total Expenses", f"₱{total:,.2f}"),
        ("Transactions", str(total_count)),
        ("Average", f"₱{avg_expense:,.2f}"),
    ]))
    elements.append(Spacer(1, 10))

    headers = ["Trip Ref", "Truck", "Type", "Amount", "Date", "Notes"]
    rows = []
    for e in expenses:
        rows.append([
            Paragraph(e.trip.reference_number if e.trip else "-", s["tc"]),
            Paragraph(e.truck.plate_number if e.truck else "-", s["tc"]),
            Paragraph(e.get_expense_type_display(), s["tcc"]),
            Paragraph(f"₱{e.amount:,.2f}", s["tcr"]),
            Paragraph(_fmt_date(e.date), s["tcc"]),
            Paragraph(e.notes or "-", s["tc"]),
        ])
    elements.append(portrait_build_table(s, headers, rows))
    return make_portrait_pdf_response("expense_report.pdf", elements, "Expense Report")


@login_required
def payment_pdf(request):
    start, end = get_date_range(request)
    payments = Payment.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
    status = request.GET.get("status", "")
    if status:
        payments = payments.filter(payment_status=status)
    total_collected = payments.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    total_due = payments.aggregate(Sum("amount_due"))["amount_due__sum"] or 0
    outstanding = total_due - total_collected
    s = portrait_style_sheet()
    elements = []
    portrait_title_block(s, elements, "Payment Report", period=_range_str(start, end))

    elements.append(portrait_multi_statRow(s, [
        ("Total Collected", f"₱{total_collected:,.2f}"),
        ("Total Due", f"₱{total_due:,.2f}"),
        ("Outstanding", f"₱{outstanding:,.2f}"),
    ]))
    elements.append(Spacer(1, 10))

    headers = ["Trip Ref", "Client", "Amount Due", "Amount Paid", "Balance", "Status", "Date", "Method"]
    rows = []
    for p in payments:
        rows.append([
            Paragraph(p.trip.reference_number if p.trip else "-", s["tc"]),
            Paragraph(p.client.client_name if p.client else "-", s["tc"]),
            Paragraph(f"₱{p.amount_due:,.2f}", s["tcr"]),
            Paragraph(f"₱{p.amount_paid:,.2f}", s["tcr"]),
            Paragraph(f"₱{p.amount_due - p.amount_paid:,.2f}", s["tcr"]),
            Paragraph(p.get_payment_status_display(), s["tcc"]),
            Paragraph(_fmt_date(p.payment_date) if p.payment_date else "-", s["tcc"]),
            Paragraph(p.payment_method or "-", s["tcc"]),
        ])
    elements.append(portrait_build_table(s, headers, rows))
    return make_portrait_pdf_response("payment_report.pdf", elements, "Payment Report")


@login_required
def profit_loss_pdf(request):
    start, end = get_date_range(request)
    revenue = Payment.objects.filter(
        payment_date__gte=start, payment_date__lte=end, payment_status="paid"
    ).aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    expenses_total = Expense.objects.filter(
        date__gte=start, date__lte=end
    ).aggregate(Sum("amount"))["amount__sum"] or 0
    profit = revenue - expenses_total
    s = portrait_style_sheet()
    elements = []
    portrait_title_block(s, elements, "Profit & Loss Report", period=_range_str(start, end))

    GREEN_OK = HexColor("#16A34A")
    RED_BAD = HexColor("#DC2626")
    profit_color = GREEN_OK if profit >= 0 else RED_BAD
    profit_label = "Net Profit" if profit >= 0 else "Net Loss"
    margin = ((profit / revenue) * 100) if revenue > 0 else 0

    elements.append(portrait_multi_statRow(s, [
        ("Total Revenue", f"₱{revenue:,.2f}"),
        ("Total Expenses", f"₱{expenses_total:,.2f}"),
        (profit_label, f"₱{profit:,.2f}"),
    ]))
    elements.append(Spacer(1, 10))

    profit_style = ParagraphStyle("PV", parent=s["kpi_value"], textColor=profit_color)
    summary_data = [
        [Paragraph("Profit Margin", s["kpi_label"]), Paragraph(f"{margin:.1f}%", profit_style)],
    ]
    tw = PAGE_W_P - PORTRAIT_MARGIN * 2
    summary_tbl = Table(summary_data, colWidths=[tw])
    summary_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, ACCENT_LINE),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(summary_tbl)

    return make_portrait_pdf_response("profit_loss.pdf", elements, "Profit & Loss Report")
