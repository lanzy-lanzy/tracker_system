from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from .models import Expense
from trips.models import Trip
from trucks.models import Truck


@login_required
def expense_list_view(request):
    expenses = Expense.objects.all().select_related("trip", "truck")
    return render(request, "expenses/expense_list.html", {"expenses": expenses})


@login_required
def expense_create_view(request):
    if request.method == "POST":
        Expense.objects.create(
            trip_id=request.POST.get("trip") or None,
            truck_id=request.POST.get("truck") or None,
            expense_type=request.POST.get("expense_type"),
            amount=request.POST.get("amount"),
            date=request.POST.get("date"),
            receipt=request.FILES.get("receipt"),
            notes=request.POST.get("notes"),
        )
        messages.success(request, "Expense recorded.")
        return redirect("expense_list")
    trips = Trip.objects.all()
    trucks = Truck.objects.all()
    return render(request, "expenses/expense_form.html", {"trips": trips, "trucks": trucks})


@login_required
def expense_edit_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.trip_id = request.POST.get("trip") or None
        expense.truck_id = request.POST.get("truck") or None
        expense.expense_type = request.POST.get("expense_type")
        expense.amount = request.POST.get("amount")
        expense.date = request.POST.get("date")
        if request.FILES.get("receipt"):
            expense.receipt = request.FILES["receipt"]
        expense.notes = request.POST.get("notes")
        expense.save()
        messages.success(request, "Expense updated.")
        return redirect("expense_list")
    trips = Trip.objects.all()
    trucks = Truck.objects.all()
    return render(request, "expenses/expense_form.html", {
        "expense": expense, "trips": trips, "trucks": trucks
    })


@login_required
def expense_delete_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Expense deleted.")
        return redirect("expense_list")
    return render(request, "expenses/expense_confirm_delete.html", {"expense": expense})


@login_required
def expense_modal_create(request):
    trips = Trip.objects.all()
    trucks = Truck.objects.all()
    if request.method == "POST":
        try:
            Expense.objects.create(
                trip_id=request.POST.get("trip") or None,
                truck_id=request.POST.get("truck") or None,
                expense_type=request.POST.get("expense_type"),
                amount=request.POST.get("amount"),
                date=request.POST.get("date"),
                receipt=request.FILES.get("receipt"),
                notes=request.POST.get("notes"),
            )
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("expense_list")
            return response
        except Exception as e:
            return render(request, "expenses/_form.html", {
                "form_expense": None, "trips": trips, "trucks": trucks,
                "action_url": reverse("expense_modal_create"), "error": str(e),
            })
    return render(request, "expenses/_form.html", {
        "form_expense": None, "trips": trips, "trucks": trucks,
        "action_url": reverse("expense_modal_create"),
    })


@login_required
def expense_modal_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    trips = Trip.objects.all()
    trucks = Truck.objects.all()
    if request.method == "POST":
        try:
            expense.trip_id = request.POST.get("trip") or None
            expense.truck_id = request.POST.get("truck") or None
            expense.expense_type = request.POST.get("expense_type")
            expense.amount = request.POST.get("amount")
            expense.date = request.POST.get("date")
            if request.FILES.get("receipt"):
                expense.receipt = request.FILES["receipt"]
            expense.notes = request.POST.get("notes")
            expense.save()
            response = HttpResponse()
            response["HX-Trigger"] = "closeModal"
            response["HX-Redirect"] = reverse("expense_list")
            return response
        except Exception as e:
            return render(request, "expenses/_form.html", {
                "form_expense": expense, "trips": trips, "trucks": trucks,
                "action_url": reverse("expense_modal_edit", args=[pk]), "error": str(e),
            })
    return render(request, "expenses/_form.html", {
        "form_expense": expense, "trips": trips, "trucks": trucks,
        "action_url": reverse("expense_modal_edit", args=[pk]),
    })


@login_required
def expense_modal_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        response = HttpResponse()
        response["HX-Trigger"] = "closeModal"
        response["HX-Redirect"] = reverse("expense_list")
        return response
    return render(request, "expenses/_delete.html", {
        "object": expense, "action_url": reverse("expense_modal_delete", args=[pk]),
    })
