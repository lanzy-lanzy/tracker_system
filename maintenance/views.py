import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from .models import Maintenance
from core.decorators import role_required
from trucks.models import Truck

logger = logging.getLogger(__name__)


@login_required
def maintenance_list_view(request):
    records = Maintenance.objects.all().select_related("truck")
    return render(request, "maintenance/maintenance_list.html", {"records": records})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def maintenance_create_view(request):
    if request.method == "POST":
        Maintenance.objects.create(
            truck_id=request.POST.get("truck"),
            maintenance_type=request.POST.get("maintenance_type"),
            description=request.POST.get("description"),
            service_date=request.POST.get("service_date"),
            next_service_date=request.POST.get("next_service_date") or None,
            cost=request.POST.get("cost") or None,
            service_provider=request.POST.get("service_provider"),
            status=request.POST.get("status", "scheduled"),
            remarks=request.POST.get("remarks"),
        )
        messages.success(request, "Maintenance record added.")
        return redirect("maintenance_list")
    trucks = Truck.objects.all()
    return render(request, "maintenance/maintenance_form.html", {"trucks": trucks})


@login_required
def maintenance_detail_view(request, pk):
    record = get_object_or_404(Maintenance.objects.select_related("truck"), pk=pk)
    return render(request, "maintenance/maintenance_detail.html", {"record": record})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def maintenance_edit_view(request, pk):
    record = get_object_or_404(Maintenance, pk=pk)
    if request.method == "POST":
        record.truck_id = request.POST.get("truck")
        record.maintenance_type = request.POST.get("maintenance_type")
        record.description = request.POST.get("description")
        record.service_date = request.POST.get("service_date")
        record.next_service_date = request.POST.get("next_service_date") or None
        record.cost = request.POST.get("cost") or None
        record.service_provider = request.POST.get("service_provider")
        record.status = request.POST.get("status")
        record.remarks = request.POST.get("remarks")
        record.save()
        messages.success(request, "Maintenance record updated.")
        return redirect("maintenance_list")
    trucks = Truck.objects.all()
    return render(request, "maintenance/maintenance_form.html", {"record": record, "trucks": trucks})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def maintenance_delete_view(request, pk):
    record = get_object_or_404(Maintenance, pk=pk)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Maintenance record deleted.")
        return redirect("maintenance_list")
    return render(request, "maintenance/maintenance_confirm_delete.html", {"record": record})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def maintenance_modal_create(request):
    trucks = Truck.objects.all()
    if request.method == "POST":
        try:
            Maintenance.objects.create(
                truck_id=request.POST.get("truck"),
                maintenance_type=request.POST.get("maintenance_type"),
                description=request.POST.get("description"),
                service_date=request.POST.get("service_date"),
                next_service_date=request.POST.get("next_service_date") or None,
                cost=request.POST.get("cost") or None,
                service_provider=request.POST.get("service_provider"),
                status=request.POST.get("status", "scheduled"),
                remarks=request.POST.get("remarks"),
            )
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("maintenance_list")
            return response
        except Exception as e:
            logger.exception("Error creating maintenance record")
            return render(request, "maintenance/_form.html", {
                "form_record": None, "trucks": trucks,
                "action_url": reverse("maintenance_modal_create"), "error": "An unexpected error occurred. Please check your input.",
            })
    return render(request, "maintenance/_form.html", {
        "form_record": None, "trucks": trucks,
        "action_url": reverse("maintenance_modal_create"),
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def maintenance_modal_edit(request, pk):
    record = get_object_or_404(Maintenance, pk=pk)
    trucks = Truck.objects.all()
    if request.method == "POST":
        try:
            record.truck_id = request.POST.get("truck")
            record.maintenance_type = request.POST.get("maintenance_type")
            record.description = request.POST.get("description")
            record.service_date = request.POST.get("service_date")
            record.next_service_date = request.POST.get("next_service_date") or None
            record.cost = request.POST.get("cost") or None
            record.service_provider = request.POST.get("service_provider")
            record.status = request.POST.get("status")
            record.remarks = request.POST.get("remarks")
            record.save()
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("maintenance_list")
            return response
        except Exception as e:
            logger.exception("Error editing maintenance record %s", pk)
            return render(request, "maintenance/_form.html", {
                "form_record": record, "trucks": trucks,
                "action_url": reverse("maintenance_modal_edit", args=[pk]), "error": "An unexpected error occurred. Please check your input.",
            })
    return render(request, "maintenance/_form.html", {
        "form_record": record, "trucks": trucks,
        "action_url": reverse("maintenance_modal_edit", args=[pk]),
    })


@login_required
def maintenance_modal_detail(request, pk):
    record = get_object_or_404(Maintenance.objects.select_related("truck"), pk=pk)
    return render(request, "maintenance/_detail.html", {"record": record})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def maintenance_modal_delete(request, pk):
    record = get_object_or_404(Maintenance, pk=pk)
    if request.method == "POST":
        record.delete()
        response = HttpResponse()
        response["HX-Trigger"] = "closeModal"
        response["HX-Redirect"] = reverse("maintenance_list")
        return response
    return render(request, "maintenance/_delete.html", {
        "object": record, "action_url": reverse("maintenance_modal_delete", args=[pk]),
    })
