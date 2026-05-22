from django.db import models
from django.utils import timezone
from trucks.models import Truck


class Maintenance(models.Model):
    MAINTENANCE_TYPES = [
        ("routine", "Routine Check"),
        ("oil_change", "Oil Change"),
        ("tire", "Tire Replacement"),
        ("brake", "Brake Service"),
        ("engine", "Engine Repair"),
        ("transmission", "Transmission Service"),
        ("electrical", "Electrical Repair"),
        ("body", "Body Repair"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name="maintenance_records")
    maintenance_type = models.CharField(max_length=30, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    service_date = models.DateField()
    next_service_date = models.DateField(blank=True, null=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    service_provider = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-service_date"]

    def __str__(self):
        return f"{self.truck.plate_number} - {self.get_maintenance_type_display()}"

    def is_overdue(self):
        if self.next_service_date and self.status != "completed":
            return self.next_service_date < timezone.now().date()
        return False

    def days_until_due(self):
        if self.next_service_date:
            delta = self.next_service_date - timezone.now().date()
            return delta.days
        return None
