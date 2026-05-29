from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from .models import Truck
from core.decorators import role_required
from maintenance.models import Maintenance
from trips.models import Trip


@login_required
def truck_list_view(request):
    trucks = Truck.objects.all()
    return render(request, "trucks/truck_list.html", {"trucks": trucks})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def truck_create_view(request):
    if request.method == "POST":
        plate_number = request.POST.get("plate_number")
        if Truck.objects.filter(plate_number=plate_number).exists():
            messages.error(request, "Truck with this plate number already exists.")
        else:
            Truck.objects.create(
                plate_number=plate_number,
                unit_number=request.POST.get("unit_number"),
                truck_type=request.POST.get("truck_type"),
                capacity=request.POST.get("capacity") or None,
                year_model=request.POST.get("year_model") or None,
                registration_number=request.POST.get("registration_number"),
                registration_expiry=request.POST.get("registration_expiry") or None,
                insurance_expiry=request.POST.get("insurance_expiry") or None,
                status=request.POST.get("status", "available"),
                remarks=request.POST.get("remarks"),
            )
            messages.success(request, "Truck added successfully.")
            return redirect("truck_list")
    return render(request, "trucks/truck_form.html")


@login_required
def truck_detail_view(request, pk):
    truck = get_object_or_404(Truck, pk=pk)
    maintenance_records = Maintenance.objects.filter(truck=truck)[:10]
    trip_history = Trip.objects.filter(assigned_truck=truck)[:10]
    return render(request, "trucks/truck_detail.html", {
        "truck": truck,
        "maintenance_records": maintenance_records,
        "trip_history": trip_history,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def truck_edit_view(request, pk):
    truck = get_object_or_404(Truck, pk=pk)
    if request.method == "POST":
        truck.plate_number = request.POST.get("plate_number")
        truck.unit_number = request.POST.get("unit_number")
        truck.truck_type = request.POST.get("truck_type")
        truck.capacity = request.POST.get("capacity") or None
        truck.year_model = request.POST.get("year_model") or None
        truck.registration_number = request.POST.get("registration_number")
        truck.registration_expiry = request.POST.get("registration_expiry") or None
        truck.insurance_expiry = request.POST.get("insurance_expiry") or None
        truck.status = request.POST.get("status")
        truck.remarks = request.POST.get("remarks")
        truck.save()
        messages.success(request, "Truck updated successfully.")
        return redirect("truck_detail", pk=truck.pk)
    return render(request, "trucks/truck_form.html", {"truck": truck})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def truck_delete_view(request, pk):
    truck = get_object_or_404(Truck, pk=pk)
    if request.method == "POST":
        truck.delete()
        messages.success(request, "Truck deleted successfully.")
        return redirect("truck_list")
    return render(request, "trucks/truck_confirm_delete.html", {"truck": truck})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def truck_modal_create(request):
    if request.method == "POST":
        plate = request.POST.get("plate_number")
        if Truck.objects.filter(plate_number=plate).exists():
            return render(request, "trucks/_form.html", {
                "error": "Plate number exists",
                "action_url": "truck_modal_create",
                "truck_types": Truck.TRUCK_TYPES,
                "status_choices": Truck.STATUS_CHOICES,
            })
        Truck.objects.create(
            plate_number=plate,
            unit_number=request.POST.get("unit_number"),
            truck_type=request.POST.get("truck_type"),
            capacity=request.POST.get("capacity") or None,
            year_model=request.POST.get("year_model") or None,
            registration_number=request.POST.get("registration_number"),
            registration_expiry=request.POST.get("registration_expiry") or None,
            insurance_expiry=request.POST.get("insurance_expiry") or None,
            status=request.POST.get("status", "available"),
            remarks=request.POST.get("remarks"),
        )
        messages.success(request, "Truck added successfully.")
        response = HttpResponse()
        response["HX-Redirect"] = reverse("truck_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "trucks/_form.html", {
        "action_url": "truck_modal_create",
        "truck_types": Truck.TRUCK_TYPES,
        "status_choices": Truck.STATUS_CHOICES,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def truck_modal_edit(request, pk):
    truck = get_object_or_404(Truck, pk=pk)
    if request.method == "POST":
        truck.plate_number = request.POST.get("plate_number")
        truck.unit_number = request.POST.get("unit_number")
        truck.truck_type = request.POST.get("truck_type")
        truck.capacity = request.POST.get("capacity") or None
        truck.year_model = request.POST.get("year_model") or None
        truck.registration_number = request.POST.get("registration_number")
        truck.registration_expiry = request.POST.get("registration_expiry") or None
        truck.insurance_expiry = request.POST.get("insurance_expiry") or None
        truck.status = request.POST.get("status")
        truck.remarks = request.POST.get("remarks")
        truck.save()
        messages.success(request, "Truck updated successfully.")
        response = HttpResponse()
        response["HX-Redirect"] = reverse("truck_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "trucks/_form.html", {
        "form_truck": truck,
        "action_url": "truck_modal_edit",
        "pk": pk,
        "truck_types": Truck.TRUCK_TYPES,
        "status_choices": Truck.STATUS_CHOICES,
    })


@login_required
def truck_modal_detail(request, pk):
    truck = get_object_or_404(Truck, pk=pk)
    return render(request, "trucks/_detail.html", {"truck": truck})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def truck_modal_delete(request, pk):
    truck = get_object_or_404(Truck, pk=pk)
    if request.method == "POST":
        truck.delete()
        messages.success(request, "Truck deleted successfully.")
        response = HttpResponse()
        response["HX-Redirect"] = reverse("truck_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "trucks/_delete.html", {"truck": truck, "action_url": "truck_modal_delete", "pk": pk})
