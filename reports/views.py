from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from trips.models import Trip
from trucks.models import Truck
from drivers.models import Driver
from maintenance.models import Maintenance
from expenses.models import Expense
from payments.models import Payment
from clients.models import Client

from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.colors import HexColor
from .pdf_utils import (
    make_pdf_response, add_title, _build_table, _stat_block,
    styles, table_cell_style, table_cell_center, table_cell_right,
    PRIMARY, DARK, GREEN, RED, ParagraphStyle,
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


def _rows_for_trips(trips):
    rows = []
    for t in trips:
        rows.append([
            Paragraph(t.reference_number or "-", table_cell_style),
            Paragraph(t.client.client_name if t.client else "-", table_cell_style),
            Paragraph(t.assigned_driver.full_name if t.assigned_driver else "-", table_cell_style),
            Paragraph(t.pickup_location or "-", table_cell_style),
            Paragraph(t.dropoff_location or "-", table_cell_style),
            Paragraph(t.get_status_display(), table_cell_center),
            Paragraph(_fmt_date(t.scheduled_delivery) if t.scheduled_delivery else "-", table_cell_center),
        ])
    return rows


@login_required
def report_dashboard_view(request):
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
    trucks = Truck.objects.annotate(
        total_trips=Count("trips"),
        completed_trips=Count("trips", filter=Q(trips__status="delivered")),
    )
    return render(request, "reports/truck_utilization.html", {"trucks": trucks})


@login_required
def driver_performance_report(request):
    drivers = Driver.objects.annotate(
        total_trips=Count("trips"),
        completed_trips=Count("trips", filter=Q(trips__status="delivered")),
    )
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


# --- PDF views ---

@login_required
def daily_trip_pdf(request):
    start, end = get_date_range(request)
    trips = Trip.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
    status_filter = request.GET.get("status", "")
    if status_filter:
        trips = trips.filter(status=status_filter)
    elements = []
    add_title(elements, "Daily Trip Report", date_range=_range_str(start, end))
    elements.append(Paragraph(f"<b>Total Trips:</b> {trips.count()}", table_cell_style))
    elements.append(Spacer(1, 8))
    headers = ["Ref#", "Client", "Driver", "Pickup", "Dropoff", "Status", "Scheduled Delivery"]
    col_widths = [55, 70, 70, 80, 80, 55, 65]
    rows = _rows_for_trips(trips)
    if rows:
        elements.append(_build_table(headers, rows, col_widths))
    else:
        elements.append(Paragraph("No trips found for the selected period.", table_cell_style))
    return make_pdf_response("daily_trip_report.pdf", elements)


@login_required
def monthly_trip_pdf(request):
    start, end = get_date_range(request)
    trips = Trip.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
    total = trips.count()
    completed = trips.filter(status="delivered").count()
    cancelled = trips.filter(status="cancelled").count()
    in_transit = trips.filter(status="in_transit").count()
    elements = []
    add_title(elements, "Monthly Trip Report", date_range=_range_str(start, end))
    elements.append(Paragraph(
        f"Total: <b>{total}</b>  |  "
        f"Completed: <b>{completed}</b>  |  "
        f"In Transit: <b>{in_transit}</b>  |  "
        f"Cancelled: <b>{cancelled}</b>",
        table_cell_style
    ))
    elements.append(Spacer(1, 8))
    headers = ["Ref#", "Client", "Driver", "Pickup", "Dropoff", "Status", "Scheduled Delivery"]
    col_widths = [55, 70, 70, 80, 80, 55, 65]
    rows = _rows_for_trips(trips)
    if rows:
        elements.append(_build_table(headers, rows, col_widths))
    else:
        elements.append(Paragraph("No trips found for the selected period.", table_cell_style))
    return make_pdf_response("monthly_trip_report.pdf", elements)


@login_required
def truck_utilization_pdf(request):
    trucks = Truck.objects.annotate(
        total_trips=Count("trips"),
        completed_trips=Count("trips", filter=Q(trips__status="delivered")),
    )
    elements = []
    add_title(elements, "Truck Utilization Report")
    headers = ["Plate#", "Type", "Total Trips", "Completed", "Status"]
    col_widths = [80, 100, 80, 80, 80]
    rows = []
    for truck in trucks:
        rows.append([
            Paragraph(truck.plate_number, table_cell_style),
            Paragraph(truck.get_truck_type_display() or "-", table_cell_style),
            Paragraph(str(truck.total_trips), table_cell_center),
            Paragraph(str(truck.completed_trips), table_cell_center),
            Paragraph(truck.get_status_display(), table_cell_center),
        ])
    elements.append(_build_table(headers, rows, col_widths))
    return make_pdf_response("truck_utilization.pdf", elements)


@login_required
def driver_performance_pdf(request):
    drivers = Driver.objects.annotate(
        total_trips=Count("trips"),
        completed_trips=Count("trips", filter=Q(trips__status="delivered")),
    )
    elements = []
    add_title(elements, "Driver Performance Report")
    headers = ["Driver", "Total Trips", "Completed", "Cancelled", "Completion Rate"]
    col_widths = [100, 80, 80, 80, 90]
    rows = []
    for d in drivers:
        total = d.total_trips
        completed = d.completed_trips
        cancelled = total - completed if total >= completed else 0
        rate = f"{(completed / total * 100):.1f}%" if total > 0 else "-"
        rows.append([
            Paragraph(d.full_name, table_cell_style),
            Paragraph(str(total), table_cell_center),
            Paragraph(str(completed), table_cell_center),
            Paragraph(str(cancelled), table_cell_center),
            Paragraph(rate, table_cell_center),
        ])
    elements.append(_build_table(headers, rows, col_widths))
    return make_pdf_response("driver_performance.pdf", elements)


@login_required
def maintenance_pdf(request):
    start, end = get_date_range(request)
    records = Maintenance.objects.filter(service_date__gte=start, service_date__lte=end)
    total_cost = records.aggregate(Sum("cost"))["cost__sum"] or 0
    elements = []
    add_title(elements, "Maintenance Report", date_range=_range_str(start, end))
    elements.append(Paragraph(f"<b>Total Cost:</b> P{total_cost:,.2f}", table_cell_style))
    elements.append(Spacer(1, 8))
    headers = ["Truck", "Type", "Service Date", "Cost", "Status"]
    col_widths = [80, 80, 80, 80, 70]
    rows = []
    for r in records:
        rows.append([
            Paragraph(r.truck.plate_number, table_cell_style),
            Paragraph(r.get_maintenance_type_display(), table_cell_style),
            Paragraph(_fmt_date(r.service_date), table_cell_center),
            Paragraph(f"P{r.cost:,.2f}", table_cell_right),
            Paragraph(r.get_status_display(), table_cell_center),
        ])
    elements.append(_build_table(headers, rows, col_widths))
    return make_pdf_response("maintenance_report.pdf", elements)


@login_required
def expense_pdf(request):
    start, end = get_date_range(request)
    expenses = Expense.objects.filter(date__gte=start, date__lte=end)
    expense_type = request.GET.get("expense_type", "")
    if expense_type:
        expenses = expenses.filter(expense_type=expense_type)
    total = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
    elements = []
    add_title(elements, "Expense Report", date_range=_range_str(start, end))
    elements.append(Paragraph(f"<b>Total Expenses:</b> P{total:,.2f}", table_cell_style))
    elements.append(Spacer(1, 8))
    headers = ["Trip Ref", "Truck", "Type", "Amount", "Date", "Notes"]
    col_widths = [60, 60, 60, 60, 60, 100]
    rows = []
    for e in expenses:
        rows.append([
            Paragraph(e.trip.reference_number if e.trip else "-", table_cell_style),
            Paragraph(e.truck.plate_number if e.truck else "-", table_cell_style),
            Paragraph(e.get_expense_type_display(), table_cell_center),
            Paragraph(f"P{e.amount:,.2f}", table_cell_right),
            Paragraph(_fmt_date(e.date), table_cell_center),
            Paragraph(e.notes or "-", table_cell_style),
        ])
    elements.append(_build_table(headers, rows, col_widths))
    return make_pdf_response("expense_report.pdf", elements)


@login_required
def payment_pdf(request):
    start, end = get_date_range(request)
    payments = Payment.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
    status = request.GET.get("status", "")
    if status:
        payments = payments.filter(payment_status=status)
    total_collected = payments.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    total_due = payments.aggregate(Sum("amount_due"))["amount_due__sum"] or 0
    elements = []
    add_title(elements, "Payment Report", date_range=_range_str(start, end))
    elements.append(Paragraph(
        f"Collected: <b>P{total_collected:,.2f}</b>  |  "
        f"Due: <b>P{total_due:,.2f}</b>",
        table_cell_style
    ))
    elements.append(Spacer(1, 8))
    headers = ["Trip Ref", "Client", "Amount Due", "Amount Paid", "Balance", "Status", "Date", "Method"]
    col_widths = [55, 60, 55, 55, 55, 50, 55, 50]
    rows = []
    for p in payments:
        rows.append([
            Paragraph(p.trip.reference_number if p.trip else "-", table_cell_style),
            Paragraph(p.client.client_name if p.client else "-", table_cell_style),
            Paragraph(f"P{p.amount_due:,.2f}", table_cell_right),
            Paragraph(f"P{p.amount_paid:,.2f}", table_cell_right),
            Paragraph(f"P{p.amount_due - p.amount_paid:,.2f}", table_cell_right),
            Paragraph(p.get_payment_status_display(), table_cell_center),
            Paragraph(_fmt_date(p.payment_date) if p.payment_date else "-", table_cell_center),
            Paragraph(p.payment_method or "-", table_cell_center),
        ])
    elements.append(_build_table(headers, rows, col_widths))
    return make_pdf_response("payment_report.pdf", elements)


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
    elements = []
    add_title(elements, "Profit & Loss Report", date_range=_range_str(start, end))
    profit_color = GREEN if profit >= 0 else RED
    profit_label = "Net Profit" if profit >= 0 else "Net Loss"
    stat_data = [
        [Paragraph("Total Revenue", table_cell_style), Paragraph(f"P{revenue:,.2f}", table_cell_right)],
        [Paragraph("Total Expenses", table_cell_style), Paragraph(f"P{expenses_total:,.2f}", table_cell_right)],
        [Paragraph(f"<b>{profit_label}</b>", table_cell_style),
         Paragraph(f"<b>P{profit:,.2f}</b>", ParagraphStyle("pr", parent=table_cell_right, textColor=profit_color))],
    ]
    t = Table(stat_data, colWidths=[150, 120])
    t.setStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#DCC3AA")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -2), HexColor("#F9FAFB")),
    ])
    elements.append(t)
    return make_pdf_response("profit_loss.pdf", elements)
