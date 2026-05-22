from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from .models import Payment
from trips.models import Trip
from clients.models import Client


@login_required
def payment_list_view(request):
    payments = Payment.objects.all().select_related("trip", "client")
    return render(request, "payments/payment_list.html", {"payments": payments})


@login_required
def payment_create_view(request):
    if request.method == "POST":
        trip = get_object_or_404(Trip, pk=request.POST.get("trip"))
        Payment.objects.create(
            trip=trip,
            client_id=request.POST.get("client"),
            amount_due=request.POST.get("amount_due"),
            amount_paid=request.POST.get("amount_paid", 0),
            payment_date=request.POST.get("payment_date") or None,
            payment_method=request.POST.get("payment_method"),
            notes=request.POST.get("notes"),
        )
        messages.success(request, "Payment recorded.")
        return redirect("payment_list")
    trips = Trip.objects.all()
    clients = Client.objects.all()
    return render(request, "payments/payment_form.html", {"trips": trips, "clients": clients})


@login_required
def payment_edit_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == "POST":
        payment.trip_id = request.POST.get("trip")
        payment.client_id = request.POST.get("client")
        payment.amount_due = request.POST.get("amount_due")
        payment.amount_paid = request.POST.get("amount_paid", 0)
        payment.payment_date = request.POST.get("payment_date") or None
        payment.payment_method = request.POST.get("payment_method")
        payment.notes = request.POST.get("notes")
        payment.save()
        messages.success(request, "Payment updated.")
        return redirect("payment_list")
    trips = Trip.objects.all()
    clients = Client.objects.all()
    return render(request, "payments/payment_form.html", {
        "payment": payment, "trips": trips, "clients": clients
    })


@login_required
def payment_delete_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == "POST":
        payment.delete()
        messages.success(request, "Payment deleted.")
        return redirect("payment_list")
    return render(request, "payments/payment_confirm_delete.html", {"payment": payment})


@login_required
def payment_modal_create(request):
    trips = Trip.objects.all()
    clients = Client.objects.all()
    if request.method == "POST":
        try:
            trip = get_object_or_404(Trip, pk=request.POST.get("trip"))
            Payment.objects.create(
                trip=trip,
                client_id=request.POST.get("client"),
                amount_due=request.POST.get("amount_due"),
                amount_paid=request.POST.get("amount_paid", 0),
                payment_date=request.POST.get("payment_date") or None,
                payment_method=request.POST.get("payment_method"),
                notes=request.POST.get("notes"),
            )
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("payment_list")
            return response
        except Exception as e:
            return render(request, "payments/_form.html", {
                "form_payment": None, "trips": trips, "clients": clients,
                "action_url": reverse("payment_modal_create"), "error": str(e),
            })
    return render(request, "payments/_form.html", {
        "form_payment": None, "trips": trips, "clients": clients,
        "action_url": reverse("payment_modal_create"),
    })


@login_required
def payment_modal_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    trips = Trip.objects.all()
    clients = Client.objects.all()
    if request.method == "POST":
        try:
            payment.trip_id = request.POST.get("trip")
            payment.client_id = request.POST.get("client")
            payment.amount_due = request.POST.get("amount_due")
            payment.amount_paid = request.POST.get("amount_paid", 0)
            payment.payment_date = request.POST.get("payment_date") or None
            payment.payment_method = request.POST.get("payment_method")
            payment.notes = request.POST.get("notes")
            payment.save()
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("payment_list")
            return response
        except Exception as e:
            return render(request, "payments/_form.html", {
                "form_payment": payment, "trips": trips, "clients": clients,
                "action_url": reverse("payment_modal_edit", args=[pk]), "error": str(e),
            })
    return render(request, "payments/_form.html", {
        "form_payment": payment, "trips": trips, "clients": clients,
        "action_url": reverse("payment_modal_edit", args=[pk]),
    })


@login_required
def payment_modal_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == "POST":
        payment.delete()
        response = HttpResponse()
        response["HX-Trigger"] = "closeModal"
        response["HX-Redirect"] = reverse("payment_list")
        return response
    return render(request, "payments/_delete.html", {
        "object": payment, "action_url": reverse("payment_modal_delete", args=[pk]),
    })
