from django.db import models
from trips.models import Trip


class Cargo(models.Model):
    CONDITION_CHOICES = [
        ("excellent", "Excellent"),
        ("good", "Good"),
        ("fair", "Fair"),
        ("damaged", "Damaged"),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="cargo_items")
    cargo_type = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    quantity = models.IntegerField(blank=True, null=True)
    special_handling = models.TextField(blank=True, null=True, verbose_name="Special Handling Instructions")
    condition_before = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    condition_after = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.cargo_type} - {self.trip.reference_number}"
