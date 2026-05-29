from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from clients.models import Client
from trucks.models import Truck
from drivers.models import Driver


TRIP_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("scheduled", "Scheduled"),
    ("loading", "Loading"),
    ("in_transit", "In Transit"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
]


class StatusHistory(models.Model):
    trip = models.ForeignKey("Trip", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=TRIP_STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name_plural = "Status histories"

    def __str__(self):
        return f"{self.trip.reference_number} → {self.get_status_display()}"


class Trip(models.Model):
    STATUS_CHOICES = TRIP_STATUS_CHOICES

    reference_number = models.CharField(max_length=50, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="trips")
    assigned_truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True, blank=True, related_name="trips")
    assigned_driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="trips")
    pickup_location = models.TextField()
    dropoff_location = models.TextField()
    cargo_description = models.TextField(blank=True, null=True)
    cargo_weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    cargo_quantity = models.IntegerField(blank=True, null=True)
    scheduled_pickup = models.DateTimeField()
    scheduled_delivery = models.DateTimeField()
    actual_pickup = models.DateTimeField(blank=True, null=True)
    actual_delivery = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    delivery_proof = models.FileField(
        upload_to="delivery_proofs/", blank=True, null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "pdf", "doc", "docx"])],
    )
    remarks = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_trips")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference_number

    def save(self, *args, **kwargs):
        if not self.reference_number:
            today = timezone.now()
            date_part = today.strftime("%Y%m%d")
            count = Trip.objects.filter(created_at__date=today.date()).count() + 1
            self.reference_number = f"TRIP-{date_part}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.status not in ["delivered", "cancelled"] and self.scheduled_delivery < timezone.now():
            return True
        return False

    @property
    def duration_hours(self):
        if self.actual_pickup and self.actual_delivery:
            delta = self.actual_delivery - self.actual_pickup
            return round(delta.total_seconds() / 3600, 2)
        return None
