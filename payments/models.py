from django.db import models
from trips.models import Trip
from clients.models import Client


class Payment(models.Model):
    STATUS_CHOICES = [
        ("unpaid", "Unpaid"),
        ("partial", "Partial"),
        ("paid", "Paid"),
    ]

    METHOD_CHOICES = [
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("check", "Check"),
        ("gcash", "G-Cash"),
        ("maya", "Maya"),
        ("other", "Other"),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="payments")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="payments")
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unpaid")
    payment_date = models.DateField(blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Reference / OR #")
    bank_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bank Name")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.trip.reference_number} - {self.client.client_name}"

    @property
    def balance(self):
        return self.amount_due - self.amount_paid

    def save(self, *args, **kwargs):
        if self.amount_paid >= self.amount_due and self.amount_paid > 0:
            self.payment_status = "paid"
        elif self.amount_paid > 0:
            self.payment_status = "partial"
        else:
            self.payment_status = "unpaid"
        super().save(*args, **kwargs)
