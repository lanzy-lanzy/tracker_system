from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


CACHE_KEYS_TO_CLEAR = set()


def register_cache_keys(*keys):
    CACHE_KEYS_TO_CLEAR.update(keys)


def _clear(*keys):
    from django.core.cache import cache
    for key in keys:
        cache.delete(key)


def invalidate_dashboard():
    _clear(
        "dashboard:summary:admin",
        "dashboard:summary:dispatcher",
        "dashboard:summary:staff",
        "dashboard:widget:trip_activity",
        "dashboard:widget:maintenance_alerts",
        "dashboard:widget:payment_summary",
    )


def invalidate_dropdowns():
    _clear("dropdown:trucks", "dropdown:drivers", "dropdown:clients")


def invalidate_reports():
    _clear("reports:utilization:trucks", "reports:performance:drivers")


@receiver(post_save, sender="trucks.Truck")
@receiver(post_delete, sender="trucks.Truck")
def truck_changed(sender, **kwargs):
    invalidate_dashboard()
    invalidate_dropdowns()
    invalidate_reports()


@receiver(post_save, sender="drivers.Driver")
@receiver(post_delete, sender="drivers.Driver")
def driver_changed(sender, **kwargs):
    invalidate_dashboard()
    invalidate_dropdowns()
    invalidate_reports()


@receiver(post_save, sender="trips.Trip")
@receiver(post_delete, sender="trips.Trip")
def trip_changed(sender, **kwargs):
    invalidate_dashboard()
    invalidate_reports()


@receiver(post_save, sender="maintenance.Maintenance")
@receiver(post_delete, sender="maintenance.Maintenance")
def maintenance_changed(sender, **kwargs):
    invalidate_dashboard()


@receiver(post_save, sender="payments.Payment")
@receiver(post_delete, sender="payments.Payment")
def payment_changed(sender, **kwargs):
    invalidate_dashboard()


@receiver(post_save, sender="expenses.Expense")
@receiver(post_delete, sender="expenses.Expense")
def expense_changed(sender, **kwargs):
    invalidate_dashboard()


@receiver(post_save, sender="clients.Client")
@receiver(post_delete, sender="clients.Client")
def client_changed(sender, **kwargs):
    invalidate_dropdowns()
