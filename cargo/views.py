import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from .models import Cargo
from core.decorators import role_required
from trips.models import Trip

logger = logging.getLogger(__name__)


@login_required
def cargo_list_view(request):
    cargo_items = Cargo.objects.all().select_related("trip")
    return render(request, "cargo/cargo_list.html", {"cargo_items": cargo_items})


@login_required
@role_required("admin", "dispatcher")
def cargo_create_view(request):
    if request.method == "POST":
        Cargo.objects.create(
            trip_id=request.POST.get("trip"),
            cargo_type=request.POST.get("cargo_type"),
            description=request.POST.get("description"),
            weight=request.POST.get("weight") or None,
            quantity=request.POST.get("quantity") or None,
            special_handling=request.POST.get("special_handling"),
            condition_before=request.POST.get("condition_before"),
            condition_after=request.POST.get("condition_after"),
        )
        messages.success(request, "Cargo record added.")
        return redirect("cargo_list")
    trips = Trip.objects.all()
    return render(request, "cargo/cargo_form.html", {"trips": trips})


@login_required
@role_required("admin", "dispatcher")
def cargo_edit_view(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == "POST":
        cargo.trip_id = request.POST.get("trip")
        cargo.cargo_type = request.POST.get("cargo_type")
        cargo.description = request.POST.get("description")
        cargo.weight = request.POST.get("weight") or None
        cargo.quantity = request.POST.get("quantity") or None
        cargo.special_handling = request.POST.get("special_handling")
        cargo.condition_before = request.POST.get("condition_before")
        cargo.condition_after = request.POST.get("condition_after")
        cargo.save()
        messages.success(request, "Cargo updated.")
        return redirect("cargo_list")
    trips = Trip.objects.all()
    return render(request, "cargo/cargo_form.html", {"cargo": cargo, "trips": trips})


@login_required
@role_required("admin", "dispatcher")
def cargo_delete_view(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == "POST":
        cargo.delete()
        messages.success(request, "Cargo deleted.")
        return redirect("cargo_list")
    return render(request, "cargo/cargo_confirm_delete.html", {"cargo": cargo})


@login_required
@role_required("admin", "dispatcher")
def cargo_modal_create(request):
    trips = Trip.objects.all()
    if request.method == "POST":
        try:
            Cargo.objects.create(
                trip_id=request.POST.get("trip"),
                cargo_type=request.POST.get("cargo_type"),
                description=request.POST.get("description"),
                weight=request.POST.get("weight") or None,
                quantity=request.POST.get("quantity") or None,
                special_handling=request.POST.get("special_handling"),
                condition_before=request.POST.get("condition_before"),
                condition_after=request.POST.get("condition_after"),
            )
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("cargo_list")
            return response
        except Exception as e:
            logger.exception("Error creating cargo")
            return render(request, "cargo/_form.html", {
                "form_cargo": None, "trips": trips,
                "action_url": reverse("cargo_modal_create"), "error": "An unexpected error occurred. Please check your input.",
            })
    return render(request, "cargo/_form.html", {
        "form_cargo": None, "trips": trips,
        "action_url": reverse("cargo_modal_create"),
    })


@login_required
@role_required("admin", "dispatcher")
def cargo_modal_edit(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    trips = Trip.objects.all()
    if request.method == "POST":
        try:
            cargo.trip_id = request.POST.get("trip")
            cargo.cargo_type = request.POST.get("cargo_type")
            cargo.description = request.POST.get("description")
            cargo.weight = request.POST.get("weight") or None
            cargo.quantity = request.POST.get("quantity") or None
            cargo.special_handling = request.POST.get("special_handling")
            cargo.condition_before = request.POST.get("condition_before")
            cargo.condition_after = request.POST.get("condition_after")
            cargo.save()
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("cargo_list")
            return response
        except Exception as e:
            logger.exception("Error editing cargo %s", pk)
            return render(request, "cargo/_form.html", {
                "form_cargo": cargo, "trips": trips,
                "action_url": reverse("cargo_modal_edit", args=[pk]), "error": "An unexpected error occurred. Please check your input.",
            })
    return render(request, "cargo/_form.html", {
        "form_cargo": cargo, "trips": trips,
        "action_url": reverse("cargo_modal_edit", args=[pk]),
    })


@login_required
@role_required("admin", "dispatcher")
def cargo_modal_delete(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == "POST":
        cargo.delete()
        response = HttpResponse()
        response["HX-Trigger"] = "closeModal"
        response["HX-Redirect"] = reverse("cargo_list")
        return response
    return render(request, "cargo/_delete.html", {
        "object": cargo, "action_url": reverse("cargo_modal_delete", args=[pk]),
    })
