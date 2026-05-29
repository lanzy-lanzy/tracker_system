from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from maintenance.models import Maintenance
from expenses.models import Expense


@receiver(post_save, sender=Maintenance)
def sync_maintenance_to_expense(sender, instance, created, **kwargs):
    if instance.status == "completed" and instance.cost is not None:
        Expense.objects.update_or_create(
            maintenance_record=instance,
            defaults={
                "truck": instance.truck,
                "expense_type": "maintenance",
                "amount": instance.cost,
                "date": instance.service_date,
                "notes": f"Maintenance: {instance.get_maintenance_type_display()} — {instance.description[:100]}",
            },
        )
    else:
        Expense.objects.filter(maintenance_record=instance).delete()


@receiver(post_delete, sender=Maintenance)
def delete_maintenance_expense(sender, instance, **kwargs):
    Expense.objects.filter(maintenance_record=instance).delete()
