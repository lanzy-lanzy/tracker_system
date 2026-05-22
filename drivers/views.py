from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.urls import reverse
from .models import Driver
from trips.models import Trip
from trucks.models import Truck


@login_required
def driver_list_view(request):
    drivers = Driver.objects.all()
    return render(request, "drivers/driver_list.html", {"drivers": drivers})


@login_required
def driver_create_view(request):
    if request.method == "POST":
        driver = Driver.objects.create(
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
    return render(request, "drivers/driver_form.html", {"trucks": trucks})


@login_required
def driver_detail_view(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    trip_history = Trip.objects.filter(assigned_driver=driver)[:10]
    return render(request, "drivers/driver_detail.html", {
        "driver": driver,
        "trip_history": trip_history,
    })


@login_required
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
        messages.success(request, "Driver updated successfully.")
        return redirect("driver_detail", pk=driver.pk)
    trucks = Truck.objects.filter(status="available") | Truck.objects.filter(pk=driver.assigned_truck_id)
    return render(request, "drivers/driver_form.html", {"driver": driver, "trucks": trucks})


@login_required
def driver_delete_view(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        driver.delete()
        messages.success(request, "Driver deleted successfully.")
        return redirect("driver_list")
    return render(request, "drivers/driver_confirm_delete.html", {"driver": driver})


@login_required
def driver_modal_create(request):
    trucks = Truck.objects.filter(status="available")
    if request.method == "POST":
        Driver.objects.create(
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


@login_required
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


@login_required
def driver_modal_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        driver.delete()
        messages.success(request, "Driver deleted successfully.")
        response = HttpResponse()
        response["HX-Redirect"] = reverse("driver_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "drivers/_delete.html", {"driver": driver, "action_url": "driver_modal_delete", "pk": pk})
