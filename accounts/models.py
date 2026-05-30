from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse


class Profile(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin / Owner"),
        ("dispatcher", "Dispatcher / Staff"),
        ("driver", "Driver"),
        ("client", "Client"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="driver")
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profiles/", blank=True, null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png"])],
    )
    profile_picture_data = models.BinaryField(blank=True, null=True, editable=False)
    profile_picture_mime_type = models.CharField(max_length=100, blank=True)
    profile_picture_filename = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

    @property
    def has_profile_picture(self):
        return bool(self.profile_picture_data) or bool(self.profile_picture)

    @property
    def profile_picture_display_url(self):
        if self.profile_picture_data:
            return reverse("profile_picture", args=[self.user_id])
        if self.profile_picture:
            return self.profile_picture.url
        return ""


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)
