from django.contrib import admin
from .models import Truck


@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ["plate_number", "unit_number", "truck_type", "capacity", "status", "registration_expiry", "insurance_expiry", "created_at"]
    list_filter = ["status", "truck_type"]
    search_fields = ["plate_number", "unit_number", "registration_number"]
