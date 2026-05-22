from django.contrib import admin
from .models import Maintenance


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ["truck", "maintenance_type", "service_date", "next_service_date", "cost", "status"]
    list_filter = ["status", "maintenance_type"]
    search_fields = ["truck__plate_number", "description"]
