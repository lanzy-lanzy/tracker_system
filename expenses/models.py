from django.db import models
from django.core.validators import FileExtensionValidator
from trips.models import Trip
from trucks.models import Truck


class Expense(models.Model):
    EXPENSE_TYPES = [
        ("fuel", "Fuel"),
        ("toll", "Toll"),
        ("repair", "Repair"),
        ("allowance", "Driver Allowance"),
        ("parking", "Parking"),
        ("other", "Other"),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    receipt = models.ImageField(
        upload_to="receipts/", blank=True, null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "pdf"])],
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.get_expense_type_display()} - {self.amount}"
