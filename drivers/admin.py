from django.contrib import admin
from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ["full_name", "contact_number", "license_number", "license_expiry", "assigned_truck", "employment_status"]
    list_filter = ["employment_status"]
    search_fields = ["full_name", "license_number", "contact_number"]
