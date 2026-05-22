from django.db import models
from django.utils import timezone


class Truck(models.Model):
    TRUCK_TYPES = [
        ("flatbed", "Flatbed"),
        ("box", "Box Truck"),
        ("refrigerated", "Refrigerated"),
        ("tanker", "Tanker"),
        ("dump", "Dump Truck"),
        ("container", "Container"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("available", "Available"),
        ("assigned", "Assigned"),
        ("on_trip", "On Trip"),
        ("maintenance", "Under Maintenance"),
        ("inactive", "Inactive"),
    ]

    plate_number = models.CharField(max_length=50, unique=True, verbose_name="Plate Number")
    unit_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Unit Number")
    truck_type = models.CharField(max_length=30, choices=TRUCK_TYPES, default="flatbed")
    capacity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Capacity in kg")
    year_model = models.IntegerField(blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    registration_expiry = models.DateField(blank=True, null=True)
    insurance_expiry = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.plate_number} - {self.get_truck_type_display()}"

    def is_registration_expired(self):
        if self.registration_expiry:
            return self.registration_expiry < timezone.now().date()
        return False

    def is_insurance_expired(self):
        if self.insurance_expiry:
            return self.insurance_expiry < timezone.now().date()
        return False

    def days_until_registration_expiry(self):
        if self.registration_expiry:
            delta = self.registration_expiry - timezone.now().date()
            return delta.days
        return None

    def days_until_insurance_expiry(self):
        if self.insurance_expiry:
            delta = self.insurance_expiry - timezone.now().date()
            return delta.days
        return None
