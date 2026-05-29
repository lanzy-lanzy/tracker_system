from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from django.template.loader import render_to_string
from .models import Trip
from core.decorators import role_required
from clients.models import Client
from trucks.models import Truck
from drivers.models import Driver
from cargo.models import Cargo


@login_required
def trip_list_view(request):
    trips = Trip.objects.all().select_related("client", "assigned_truck", "assigned_driver")
    return render(request, "trips/trip_list.html", {"trips": trips})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def trip_create_view(request):
    if request.method == "POST":
        trip = Trip.objects.create(
            client_id=request.POST.get("client"),
            assigned_truck_id=request.POST.get("assigned_truck") or None,
            assigned_driver_id=request.POST.get("assigned_driver") or None,
            pickup_location=request.POST.get("pickup_location"),
            dropoff_location=request.POST.get("dropoff_location"),
            cargo_description=request.POST.get("cargo_description"),
            cargo_weight=request.POST.get("cargo_weight") or None,
            cargo_quantity=request.POST.get("cargo_quantity") or None,
            scheduled_pickup=request.POST.get("scheduled_pickup"),
            scheduled_delivery=request.POST.get("scheduled_delivery"),
            status=request.POST.get("status", "pending"),
            remarks=request.POST.get("remarks"),
            created_by=request.user,
        )
        messages.success(request, f"Trip {trip.reference_number} created successfully.")
        return redirect("trip_detail", pk=trip.pk)
    clients = Client.objects.all()
    trucks = Truck.objects.filter(status__in=["available", "assigned"])
    drivers = Driver.objects.filter(employment_status="active")
    return render(request, "trips/trip_form.html", {
        "clients": clients,
        "trucks": trucks,
        "drivers": drivers,
    })


@login_required
def trip_detail_view(request, pk):
    trip = get_object_or_404(Trip.objects.select_related("client", "assigned_truck", "assigned_driver", "created_by"), pk=pk)
    cargo_items = Cargo.objects.filter(trip=trip)
    return render(request, "trips/trip_detail.html", {
        "trip": trip,
        "cargo_items": cargo_items,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def trip_edit_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == "POST":
        trip.client_id = request.POST.get("client")
        trip.assigned_truck_id = request.POST.get("assigned_truck") or None
        trip.assigned_driver_id = request.POST.get("assigned_driver") or None
        trip.pickup_location = request.POST.get("pickup_location")
        trip.dropoff_location = request.POST.get("dropoff_location")
        trip.cargo_description = request.POST.get("cargo_description")
        trip.cargo_weight = request.POST.get("cargo_weight") or None
        trip.cargo_quantity = request.POST.get("cargo_quantity") or None
        trip.scheduled_pickup = request.POST.get("scheduled_pickup")
        trip.scheduled_delivery = request.POST.get("scheduled_delivery")
        trip.remarks = request.POST.get("remarks")
        trip.save()
        messages.success(request, "Trip updated successfully.")
        return redirect("trip_detail", pk=trip.pk)
    clients = Client.objects.all()
    trucks = Truck.objects.filter(status__in=["available", "assigned"])
    drivers = Driver.objects.filter(employment_status="active")
    return render(request, "trips/trip_form.html", {
        "trip": trip,
        "clients": clients,
        "trucks": trucks,
        "drivers": drivers,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def trip_delete_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == "POST":
        trip.delete()
        messages.success(request, "Trip deleted successfully.")
        return redirect("trip_list")
    return render(request, "trips/trip_confirm_delete.html", {"trip": trip})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def trip_update_status(request, pk, status):
    trip = get_object_or_404(Trip, pk=pk)
    valid_statuses = dict(Trip.STATUS_CHOICES)
    if status in valid_statuses:
        trip.status = status
        if status == "in_transit" and not trip.actual_pickup:
            from django.utils import timezone
            trip.actual_pickup = timezone.now()
        if status == "delivered":
            from django.utils import timezone
            trip.actual_delivery = timezone.now()
        trip.save()
        messages.success(request, f"Trip status updated to {valid_statuses[status]}.")
    if request.headers.get("HX-Request"):
        return render(request, "trips/partials/trip_row.html", {"trip": trip})
    return redirect("trip_detail", pk=trip.pk)


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def trip_upload_proof(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == "POST" and request.FILES.get("delivery_proof"):
        trip.delivery_proof = request.FILES["delivery_proof"]
        trip.save()
        messages.success(request, "Proof of delivery uploaded.")
    return redirect("trip_detail", pk=trip.pk)


@ratelimit(key="ip", rate="30/m", method="GET", block=True)
@login_required
def trip_filter_view(request):
    status = request.GET.get("status", "")
    trips = Trip.objects.all().select_related("client", "assigned_truck", "assigned_driver")
    if status:
        trips = trips.filter(status=status)
    html = render_to_string("trips/partials/trip_table.html", {"trips": trips}, request=request)
    return HttpResponse(html)


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def trip_modal_create(request):
    if request.method == "POST":
        pickup_location = request.POST.get("pickup_location", "").strip()
        dropoff_location = request.POST.get("dropoff_location", "").strip()
        if not pickup_location or not dropoff_location:
            clients = Client.objects.all()
            trucks = Truck.objects.filter(status__in=["available", "assigned"])
            drivers = Driver.objects.filter(employment_status="active")
            return render(request, "trips/_form.html", {
                "clients": clients,
                "trucks": trucks,
                "drivers": drivers,
                "action_url": "trip_modal_create",
                "error": "Pickup and dropoff locations are required.",
            })
        trip = Trip.objects.create(
            client_id=request.POST.get("client"),
            assigned_truck_id=request.POST.get("assigned_truck") or None,
            assigned_driver_id=request.POST.get("assigned_driver") or None,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            cargo_description=request.POST.get("cargo_description", ""),
            cargo_weight=request.POST.get("cargo_weight") or None,
            cargo_quantity=request.POST.get("cargo_quantity") or None,
            scheduled_pickup=request.POST.get("scheduled_pickup"),
            scheduled_delivery=request.POST.get("scheduled_delivery"),
            status=request.POST.get("status", "pending"),
            remarks=request.POST.get("remarks", ""),
            created_by=request.user,
        )
        response = HttpResponse()
        response["HX-Redirect"] = reverse("trip_list")
        response["HX-Trigger"] = "closeModal"
        return response
    clients = Client.objects.all()
    trucks = Truck.objects.filter(status__in=["available", "assigned"])
    drivers = Driver.objects.filter(employment_status="active")
    return render(request, "trips/_form.html", {
        "clients": clients,
        "trucks": trucks,
        "drivers": drivers,
        "action_url": "trip_modal_create",
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def trip_modal_edit(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == "POST":
        trip.client_id = request.POST.get("client")
        trip.assigned_truck_id = request.POST.get("assigned_truck") or None
        trip.assigned_driver_id = request.POST.get("assigned_driver") or None
        trip.pickup_location = request.POST.get("pickup_location")
        trip.dropoff_location = request.POST.get("dropoff_location")
        trip.cargo_description = request.POST.get("cargo_description", "")
        trip.cargo_weight = request.POST.get("cargo_weight") or None
        trip.cargo_quantity = request.POST.get("cargo_quantity") or None
        trip.scheduled_pickup = request.POST.get("scheduled_pickup")
        trip.scheduled_delivery = request.POST.get("scheduled_delivery")
        trip.remarks = request.POST.get("remarks", "")
        trip.save()
        response = HttpResponse()
        response["HX-Redirect"] = reverse("trip_list")
        response["HX-Trigger"] = "closeModal"
        return response
    clients = Client.objects.all()
    trucks = Truck.objects.filter(status__in=["available", "assigned"])
    drivers = Driver.objects.filter(employment_status="active")
    return render(request, "trips/_form.html", {
        "form_trip": trip,
        "clients": clients,
        "trucks": trucks,
        "drivers": drivers,
        "action_url": "trip_modal_edit",
        "pk": pk,
    })


@login_required
def trip_modal_detail(request, pk):
    trip = get_object_or_404(Trip.objects.select_related("client", "assigned_truck", "assigned_driver"), pk=pk)
    cargo_items = Cargo.objects.filter(trip=trip)
    return render(request, "trips/_detail.html", {
        "trip": trip,
        "cargo_items": cargo_items,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def trip_modal_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == "POST":
        trip.delete()
        response = HttpResponse()
        response["HX-Redirect"] = reverse("trip_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "trips/_delete.html", {
        "trip": trip,
        "action_url": "trip_modal_delete",
    })


@ratelimit(key="ip", rate="30/m", method="GET", block=True)
@login_required
def trip_search_view(request):
    q = request.GET.get("q", "")
    trips = Trip.objects.all().select_related("client", "assigned_truck", "assigned_driver")
    if q:
        trips = trips.filter(reference_number__icontains=q) | trips.filter(
            client__client_name__icontains=q
        ) | trips.filter(pickup_location__icontains=q) | trips.filter(
            dropoff_location__icontains=q
        )
    html = render_to_string("trips/partials/trip_table.html", {"trips": trips}, request=request)
    return HttpResponse(html)
