from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from .models import Driver
from core.decorators import role_required
from core.pagination import paginate_queryset
from trips.models import Trip, StatusHistory
from trucks.models import Truck


@login_required
@role_required("admin", "dispatcher")
def driver_list_view(request):
    drivers = Driver.objects.select_related("user", "assigned_truck").order_by("full_name")
    page_obj = paginate_queryset(request, drivers)
    return render(request, "drivers/driver_list.html", {"drivers": page_obj, "page_obj": page_obj})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def driver_create_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        email = request.POST.get("email", "")
        user = None
        if username and password:
            if User.objects.filter(username=username).exists():
                trucks = Truck.objects.filter(status="available")
                return render(request, "drivers/driver_form.html", {
                    "trucks": trucks,
                    "error": "Username already taken.",
                    "employment_statuses": Driver.EMPLOYMENT_STATUS,
                })
            user = User.objects.create_user(username=username, email=email, password=password)
            user.profile.role = "driver"
            user.profile.save()
        driver = Driver.objects.create(
            user=user,
            full_name=request.POST.get("full_name"),
            contact_number=request.POST.get("contact_number"),
            address=request.POST.get("address"),
            license_number=request.POST.get("license_number"),
            license_expiry=request.POST.get("license_expiry"),
            assigned_truck_id=request.POST.get("assigned_truck") or None,
            employment_status=request.POST.get("employment_status", "active"),
            emergency_contact_name=request.POST.get("emergency_contact_name"),
            emergency_contact_number=request.POST.get("emergency_contact_number"),
            remarks=request.POST.get("remarks"),
        )
        messages.success(request, "Driver added successfully.")
        return redirect("driver_list")
    trucks = Truck.objects.filter(status="available")
    return render(request, "drivers/driver_form.html", {
        "trucks": trucks,
        "employment_statuses": Driver.EMPLOYMENT_STATUS,
    })


@login_required
def driver_detail_view(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    trip_history = Trip.objects.filter(assigned_driver=driver)[:10]
    return render(request, "drivers/driver_detail.html", {
        "driver": driver,
        "trip_history": trip_history,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def driver_edit_view(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        driver.full_name = request.POST.get("full_name")
        driver.contact_number = request.POST.get("contact_number")
        driver.address = request.POST.get("address")
        driver.license_number = request.POST.get("license_number")
        driver.license_expiry = request.POST.get("license_expiry")
        driver.assigned_truck_id = request.POST.get("assigned_truck") or None
        driver.employment_status = request.POST.get("employment_status")
        driver.emergency_contact_name = request.POST.get("emergency_contact_name")
        driver.emergency_contact_number = request.POST.get("emergency_contact_number")
        driver.remarks = request.POST.get("remarks")
        driver.save()
        user = driver.user
        if user:
            email = request.POST.get("email", "").strip()
            password = request.POST.get("password", "")
            if email:
                user.email = email
            if password:
                user.set_password(password)
            if email or password:
                user.save()
        messages.success(request, "Driver updated successfully.")
        return redirect("driver_detail", pk=driver.pk)
    trucks = Truck.objects.filter(status="available") | Truck.objects.filter(pk=driver.assigned_truck_id)
    return render(request, "drivers/driver_form.html", {
        "driver": driver,
        "trucks": trucks,
        "employment_statuses": Driver.EMPLOYMENT_STATUS,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def driver_delete_view(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        user = driver.user
        driver.delete()
        if user:
            user.delete()
            messages.success(request, "Driver and linked user account deleted.")
        else:
            messages.success(request, "Driver deleted successfully.")
        return redirect("driver_list")
    return render(request, "drivers/driver_confirm_delete.html", {"driver": driver})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def driver_modal_create(request):
    trucks = Truck.objects.filter(status="available")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        email = request.POST.get("email", "")
        user = None
        if username and password:
            if User.objects.filter(username=username).exists():
                return render(request, "drivers/_form.html", {
                    "trucks": trucks,
                    "action_url": "driver_modal_create",
                    "employment_statuses": Driver.EMPLOYMENT_STATUS,
                    "error": "Username already taken.",
                })
            user = User.objects.create_user(username=username, email=email, password=password)
            user.profile.role = "driver"
            user.profile.save()
        Driver.objects.create(
            user=user,
            full_name=request.POST.get("full_name"),
            contact_number=request.POST.get("contact_number"),
            address=request.POST.get("address"),
            license_number=request.POST.get("license_number"),
            license_expiry=request.POST.get("license_expiry"),
            assigned_truck_id=request.POST.get("assigned_truck") or None,
            employment_status=request.POST.get("employment_status", "active"),
            emergency_contact_name=request.POST.get("emergency_contact_name"),
            emergency_contact_number=request.POST.get("emergency_contact_number"),
            remarks=request.POST.get("remarks"),
        )
        messages.success(request, "Driver added successfully.")
        response = HttpResponse()
        response["HX-Redirect"] = reverse("driver_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "drivers/_form.html", {
        "trucks": trucks,
        "action_url": "driver_modal_create",
        "employment_statuses": Driver.EMPLOYMENT_STATUS,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def driver_modal_edit(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    trucks = Truck.objects.filter(status="available") | Truck.objects.filter(pk=driver.assigned_truck_id)
    if request.method == "POST":
        driver.full_name = request.POST.get("full_name")
        driver.contact_number = request.POST.get("contact_number")
        driver.address = request.POST.get("address")
        driver.license_number = request.POST.get("license_number")
        driver.license_expiry = request.POST.get("license_expiry")
        driver.assigned_truck_id = request.POST.get("assigned_truck") or None
        driver.employment_status = request.POST.get("employment_status")
        driver.emergency_contact_name = request.POST.get("emergency_contact_name")
        driver.emergency_contact_number = request.POST.get("emergency_contact_number")
        driver.remarks = request.POST.get("remarks")
        driver.save()
        user = driver.user
        if user:
            email = request.POST.get("email", "").strip()
            password = request.POST.get("password", "")
            if email:
                user.email = email
            if password:
                user.set_password(password)
            if email or password:
                user.save()
        messages.success(request, "Driver updated successfully.")
        response = HttpResponse()
        response["HX-Redirect"] = reverse("driver_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "drivers/_form.html", {
        "form_driver": driver,
        "trucks": trucks,
        "action_url": "driver_modal_edit",
        "pk": pk,
        "employment_statuses": Driver.EMPLOYMENT_STATUS,
    })


@login_required
def driver_modal_detail(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    return render(request, "drivers/_detail.html", {"driver": driver})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def driver_modal_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        user = driver.user
        driver.delete()
        if user:
            user.delete()
        messages.success(request, "Driver and linked user account deleted.")
        response = HttpResponse()
        response["HX-Redirect"] = reverse("driver_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "drivers/_delete.html", {"driver": driver, "action_url": "driver_modal_delete", "pk": pk})


@login_required
def driver_dashboard_view(request):
    role = getattr(getattr(request.user, "profile", None), "role", None)
    if role != "driver":
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    try:
        driver = request.user.driver_profile
    except Driver.DoesNotExist:
        messages.error(request, "No driver profile linked to your account.")
        return redirect("dashboard")
    today = timezone.now().date()
    all_trips = Trip.objects.filter(assigned_driver=driver).select_related("client", "assigned_truck")
    active_trips = all_trips.filter(status__in=["scheduled", "loading", "in_transit"])
    completed_trips = all_trips.filter(status__in=["delivered", "cancelled"])[:20]
    next_trip = active_trips.filter(status="scheduled").order_by("scheduled_pickup").first()
    overdue_trips = [
        t for t in active_trips
        if t.status not in ("delivered", "cancelled") and t.scheduled_delivery < timezone.now()
    ]
    stats = {
        "active_count": active_trips.count(),
        "completed_today": all_trips.filter(status="delivered", actual_delivery__date=today).count(),
        "total_delivered": all_trips.filter(status="delivered").count(),
        "overdue_count": len(overdue_trips),
    }
    recent_history = StatusHistory.objects.filter(
        trip__assigned_driver=driver
    ).select_related("trip").order_by("-timestamp")[:10]
    return render(request, "drivers/dashboard.html", {
        "driver": driver,
        "active_trips": active_trips,
        "completed_trips": completed_trips,
        "next_trip": next_trip,
        "overdue_trips": overdue_trips,
        "stats": stats,
        "recent_history": recent_history,
    })
