from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from .models import Client
from core.decorators import role_required
from trips.models import Trip
from payments.models import Payment


@login_required
def client_list_view(request):
    clients = Client.objects.all()
    return render(request, "clients/client_list.html", {"clients": clients})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def client_create_view(request):
    if request.method == "POST":
        client = Client.objects.create(
            client_name=request.POST.get("client_name"),
            contact_person=request.POST.get("contact_person"),
            contact_number=request.POST.get("contact_number"),
            email=request.POST.get("email"),
            address=request.POST.get("address"),
            company_name=request.POST.get("company_name"),
            notes=request.POST.get("notes"),
        )
        messages.success(request, "Client added successfully.")
        return redirect("client_list")
    return render(request, "clients/client_form.html")


@login_required
def client_detail_view(request, pk):
    client = get_object_or_404(Client, pk=pk)
    trips = Trip.objects.filter(client=client)[:10]
    payments = Payment.objects.filter(client=client)[:10]
    return render(request, "clients/client_detail.html", {
        "client": client,
        "trips": trips,
        "payments": payments,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def client_edit_view(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.client_name = request.POST.get("client_name")
        client.contact_person = request.POST.get("contact_person")
        client.contact_number = request.POST.get("contact_number")
        client.email = request.POST.get("email")
        client.address = request.POST.get("address")
        client.company_name = request.POST.get("company_name")
        client.notes = request.POST.get("notes")
        client.save()
        messages.success(request, "Client updated successfully.")
        return redirect("client_detail", pk=client.pk)
    return render(request, "clients/client_form.html", {"client": client})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def client_delete_view(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.delete()
        messages.success(request, "Client deleted successfully.")
        return redirect("client_list")
    return render(request, "clients/client_confirm_delete.html", {"client": client})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def client_modal_create(request):
    if request.method == "POST":
        client_name = request.POST.get("client_name", "").strip()
        if not client_name:
            return render(request, "clients/_form.html", {
                "action_url": "client_modal_create",
                "error": "Client name is required.",
            })
        client = Client.objects.create(
            client_name=client_name,
            contact_person=request.POST.get("contact_person", ""),
            contact_number=request.POST.get("contact_number", ""),
            email=request.POST.get("email", ""),
            address=request.POST.get("address", ""),
            company_name=request.POST.get("company_name", ""),
            notes=request.POST.get("notes", ""),
        )
        response = HttpResponse()
        response["HX-Redirect"] = reverse("client_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "clients/_form.html", {"action_url": "client_modal_create"})


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def client_modal_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.client_name = request.POST.get("client_name")
        client.contact_person = request.POST.get("contact_person", "")
        client.contact_number = request.POST.get("contact_number", "")
        client.email = request.POST.get("email", "")
        client.address = request.POST.get("address", "")
        client.company_name = request.POST.get("company_name", "")
        client.notes = request.POST.get("notes", "")
        client.save()
        response = HttpResponse()
        response["HX-Redirect"] = reverse("client_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "clients/_form.html", {
        "form_client": client,
        "action_url": "client_modal_edit",
        "pk": pk,
    })


@login_required
def client_modal_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    trips = Trip.objects.filter(client=client)[:5]
    payments = Payment.objects.filter(client=client)[:5]
    return render(request, "clients/_detail.html", {
        "client": client,
        "trips": trips,
        "payments": payments,
    })


@ratelimit(key="ip", rate="15/m", method="POST", block=True)
@login_required
@role_required("admin", "dispatcher")
def client_modal_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.delete()
        response = HttpResponse()
        response["HX-Redirect"] = reverse("client_list")
        response["HX-Trigger"] = "closeModal"
        return response
    return render(request, "clients/_delete.html", {
        "client": client,
        "action_url": "client_modal_delete",
    })
