from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from trucks.models import Truck
from drivers.models import Driver
from trips.models import Trip
from maintenance.models import Maintenance
from payments.models import Payment
from expenses.models import Expense
from notifications.models import Notification


@login_required
def dashboard_view(request):
    today = timezone.now().date()
    context = {
        "total_trucks": Truck.objects.count(),
        "available_trucks": Truck.objects.filter(status="available").count(),
        "maintenance_trucks": Truck.objects.filter(status="maintenance").count(),
        "total_drivers": Driver.objects.count(),
        "active_drivers": Driver.objects.filter(employment_status="active").count(),
        "active_trips": Trip.objects.filter(status__in=["scheduled", "loading", "in_transit"]).count(),
        "pending_trips": Trip.objects.filter(status="pending").count(),
        "completed_trips": Trip.objects.filter(status="delivered").count(),
        "cancelled_trips": Trip.objects.filter(status="cancelled").count(),
        "monthly_revenue": Payment.objects.filter(
            payment_date__year=today.year, payment_date__month=today.month, payment_status="paid"
        ).aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0,
        "monthly_expenses": Expense.objects.filter(
            date__year=today.year, date__month=today.month
        ).aggregate(Sum("amount"))["amount__sum"] or 0,
        "recent_trips": Trip.objects.all()[:10],
        "maintenance_alerts": Maintenance.objects.filter(status__in=["scheduled", "ongoing"]).order_by("service_date")[:5],
        "payment_summary": Payment.objects.all()[:5],
        "overdue_maintenance": Maintenance.objects.filter(
            next_service_date__lt=today, status__in=["scheduled", "ongoing"]
        ).count(),
        "expiring_registrations": Truck.objects.filter(
            registration_expiry__gte=today, registration_expiry__lte=timezone.now() + timezone.timedelta(days=30)
        ).count(),
        "unpaid_payments": Payment.objects.filter(payment_status="unpaid").count(),
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
def trip_activity_widget(request):
    trips = Trip.objects.all()[:5]
    return render(request, "dashboard/widgets/trip_activity.html", {"trips": trips})


@login_required
def maintenance_alerts_widget(request):
    alerts = Maintenance.objects.filter(status__in=["scheduled", "ongoing"]).order_by("service_date")[:5]
    return render(request, "dashboard/widgets/maintenance_alerts.html", {"alerts": alerts})


@login_required
def payment_summary_widget(request):
    payments = Payment.objects.all()[:5]
    return render(request, "dashboard/widgets/payment_summary.html", {"payments": payments})
