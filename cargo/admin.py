from django.contrib import admin
from .models import Cargo


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ["cargo_type", "trip", "weight", "quantity", "condition_before", "condition_after"]
    search_fields = ["cargo_type", "trip__reference_number"]
