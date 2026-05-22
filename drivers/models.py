from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from trucks.models import Truck


class Driver(models.Model):
    EMPLOYMENT_STATUS = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("suspended", "Suspended"),
        ("terminated", "Terminated"),
    ]

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="driver_profile")
    full_name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    license_number = models.CharField(max_length=100)
    license_expiry = models.DateField()
    assigned_truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_drivers")
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default="active")
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=20, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name

    def is_license_expired(self):
        return self.license_expiry < timezone.now().date()

    def days_until_license_expiry(self):
        delta = self.license_expiry - timezone.now().date()
        return delta.days
