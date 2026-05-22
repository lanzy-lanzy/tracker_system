from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("trip_assigned", "Trip Assigned"),
        ("trip_updated", "Trip Status Updated"),
        ("trip_completed", "Trip Completed"),
        ("maintenance_due", "Maintenance Due"),
        ("registration_expiry", "Registration Expiry"),
        ("insurance_expiry", "Insurance Expiry"),
        ("license_expiry", "License Expiry"),
        ("payment_overdue", "Payment Overdue"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user.username}"
