from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from core.utils import is_driver
from core.cache_utils import get_or_set_cache, delete_cache
from trucks.models import Truck
from drivers.models import Driver
from trips.models import Trip
from maintenance.models import Maintenance
from payments.models import Payment
from expenses.models import Expense
from notifications.models import Notification


def _build_dashboard_context():
    today = timezone.now().date()
    return {
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


@ratelimit(key="ip", rate="20/m", method="GET", block=True)
@login_required
def dashboard_view(request):
    if is_driver(request.user):
        return redirect("driver_dashboard")
    role = request.user.profile.role if hasattr(request.user, "profile") else "staff"
    cache_key = f"dashboard:summary:{role}"
    context = get_or_set_cache(cache_key, _build_dashboard_context)
    return render(request, "dashboard/dashboard.html", context)


@ratelimit(key="ip", rate="30/m", method="GET", block=True)
@login_required
def trip_activity_widget(request):
    trips = get_or_set_cache("dashboard:widget:trip_activity", lambda: list(Trip.objects.all()[:5]))
    return render(request, "dashboard/widgets/trip_activity.html", {"trips": trips})


@ratelimit(key="ip", rate="30/m", method="GET", block=True)
@login_required
def maintenance_alerts_widget(request):
    alerts = get_or_set_cache(
        "dashboard:widget:maintenance_alerts",
        lambda: list(Maintenance.objects.filter(status__in=["scheduled", "ongoing"]).order_by("service_date")[:5]),
    )
    return render(request, "dashboard/widgets/maintenance_alerts.html", {"alerts": alerts})


@ratelimit(key="ip", rate="30/m", method="GET", block=True)
@login_required
def payment_summary_widget(request):
    payments = get_or_set_cache("dashboard:widget:payment_summary", lambda: list(Payment.objects.all()[:5]))
    return render(request, "dashboard/widgets/payment_summary.html", {"payments": payments})
