import logging
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import F, Sum
from django_ratelimit.decorators import ratelimit

from .models import Payment
from core.decorators import role_required
from core.pagination import paginate_queryset
from trips.models import Trip
from clients.models import Client

logger = logging.getLogger(__name__)


def _clean_amount(value):
    if not value or str(value).strip() == "":
        return Decimal("0.00")
    cleaned = str(value).replace(",", "").strip()
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


@login_required
@role_required("admin", "dispatcher")
def payment_list_view(request):
    payments = Payment.objects.select_related("trip", "client").order_by("-payment_date", "-id")
    total_collected = payments.filter(payment_status="paid").aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    total_outstanding = payments.annotate(balance=F("amount_due") - F("amount_paid")).aggregate(Sum("balance"))["balance__sum"] or 0
    page_obj = paginate_queryset(request, payments)
    return render(request, "payments/payment_list.html", {
        "payments": page_obj,
        "page_obj": page_obj,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def payment_create_view(request):
    trips = Trip.objects.all()
    clients = Client.objects.all()
    if request.method == "POST":
        amount_due = _clean_amount(request.POST.get("amount_due"))
        amount_paid = _clean_amount(request.POST.get("amount_paid"))
        if amount_due is None or amount_due < 0:
            return render(request, "payments/payment_form.html", {
                "trips": trips, "clients": clients, "error": "Invalid amount due.",
            })
        if amount_paid is None or amount_paid < 0:
            return render(request, "payments/payment_form.html", {
                "trips": trips, "clients": clients, "error": "Invalid amount paid.",
            })
        trip = get_object_or_404(Trip, pk=request.POST.get("trip"))
        Payment.objects.create(
            trip=trip,
            client_id=request.POST.get("client"),
            amount_due=amount_due,
            amount_paid=amount_paid,
            payment_date=request.POST.get("payment_date") or None,
            payment_method=request.POST.get("payment_method"),
            reference_number=request.POST.get("reference_number", ""),
            bank_name=request.POST.get("bank_name", ""),
            notes=request.POST.get("notes"),
        )
        messages.success(request, "Payment recorded.")
        return redirect("payment_list")
    return render(request, "payments/payment_form.html", {"trips": trips, "clients": clients})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def payment_edit_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    trips = Trip.objects.all()
    clients = Client.objects.all()
    if request.method == "POST":
        amount_due = _clean_amount(request.POST.get("amount_due"))
        amount_paid = _clean_amount(request.POST.get("amount_paid"))
        if amount_due is None or amount_due < 0:
            return render(request, "payments/payment_form.html", {
                "payment": payment, "trips": trips, "clients": clients, "error": "Invalid amount due.",
            })
        if amount_paid is None or amount_paid < 0:
            return render(request, "payments/payment_form.html", {
                "payment": payment, "trips": trips, "clients": clients, "error": "Invalid amount paid.",
            })
        payment.trip_id = request.POST.get("trip")
        payment.client_id = request.POST.get("client")
        payment.amount_due = amount_due
        payment.amount_paid = amount_paid
        payment.payment_date = request.POST.get("payment_date") or None
        payment.payment_method = request.POST.get("payment_method")
        payment.reference_number = request.POST.get("reference_number", "")
        payment.bank_name = request.POST.get("bank_name", "")
        payment.notes = request.POST.get("notes")
        payment.save()
        messages.success(request, "Payment updated.")
        return redirect("payment_list")
    return render(request, "payments/payment_form.html", {
        "payment": payment, "trips": trips, "clients": clients
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def payment_delete_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == "POST":
        payment.delete()
        messages.success(request, "Payment deleted.")
        return redirect("payment_list")
    return render(request, "payments/payment_confirm_delete.html", {"payment": payment})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def payment_modal_create(request):
    trips = Trip.objects.all()
    clients = Client.objects.all()
    action_url = reverse("payment_modal_create")
    if request.method == "POST":
        amount_due = _clean_amount(request.POST.get("amount_due"))
        amount_paid = _clean_amount(request.POST.get("amount_paid"))
        errors = []
        if amount_due is None:
            errors.append("Invalid amount due.")
        if amount_paid is None:
            errors.append("Invalid amount paid.")
        if not request.POST.get("trip"):
            errors.append("Please select a trip.")
        if not request.POST.get("client"):
            errors.append("Please select a client.")
        if not request.POST.get("payment_method"):
            errors.append("Please select a payment method.")
        if errors:
            return render(request, "payments/_form.html", {
                "form_payment": None, "trips": trips, "clients": clients,
                "action_url": action_url, "error": " ".join(errors),
            })
        try:
            trip = get_object_or_404(Trip, pk=request.POST.get("trip"))
            Payment.objects.create(
                trip=trip,
                client_id=request.POST.get("client"),
                amount_due=amount_due,
                amount_paid=amount_paid,
                payment_date=request.POST.get("payment_date") or None,
                payment_method=request.POST.get("payment_method"),
                reference_number=request.POST.get("reference_number", ""),
                bank_name=request.POST.get("bank_name", ""),
                notes=request.POST.get("notes"),
            )
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("payment_list")
            return response
        except Exception as e:
            logger.exception("Error creating payment")
            return render(request, "payments/_form.html", {
                "form_payment": None, "trips": trips, "clients": clients,
                "action_url": action_url, "error": "An unexpected error occurred. Please check your input.",
            })
    return render(request, "payments/_form.html", {
        "form_payment": None, "trips": trips, "clients": clients,
        "action_url": action_url,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def payment_modal_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    trips = Trip.objects.all()
    clients = Client.objects.all()
    action_url = reverse("payment_modal_edit", args=[pk])
    if request.method == "POST":
        amount_due = _clean_amount(request.POST.get("amount_due"))
        amount_paid = _clean_amount(request.POST.get("amount_paid"))
        errors = []
        if amount_due is None:
            errors.append("Invalid amount due.")
        if amount_paid is None:
            errors.append("Invalid amount paid.")
        if errors:
            return render(request, "payments/_form.html", {
                "form_payment": payment, "trips": trips, "clients": clients,
                "action_url": action_url, "error": " ".join(errors),
            })
        try:
            payment.trip_id = request.POST.get("trip")
            payment.client_id = request.POST.get("client")
            payment.amount_due = amount_due
            payment.amount_paid = amount_paid
            payment.payment_date = request.POST.get("payment_date") or None
            payment.payment_method = request.POST.get("payment_method")
            payment.reference_number = request.POST.get("reference_number", "")
            payment.bank_name = request.POST.get("bank_name", "")
            payment.notes = request.POST.get("notes")
            payment.save()
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("payment_list")
            return response
        except Exception as e:
            logger.exception("Error editing payment %s", pk)
            return render(request, "payments/_form.html", {
                "form_payment": payment, "trips": trips, "clients": clients,
                "action_url": action_url, "error": "An unexpected error occurred. Please check your input.",
            })
    return render(request, "payments/_form.html", {
        "form_payment": payment, "trips": trips, "clients": clients,
        "action_url": action_url,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
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
