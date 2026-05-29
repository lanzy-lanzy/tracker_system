from django.db import migrations, models


def map_payment_methods(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    mapping = {
        "Check": "check",
        "Bank Transfer": "bank_transfer",
        "Cash": "cash",
        "G-Cash": "gcash",
        "Maya": "maya",
        "Other": "other",
        "Bank Transfer ": "bank_transfer",
    }
    for payment in Payment.objects.all():
        if payment.payment_method in mapping:
            payment.payment_method = mapping[payment.payment_method]
            payment.save(update_fields=["payment_method"])


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="bank_name",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Bank Name"
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="reference_number",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Reference / OR #"
            ),
        ),
        migrations.RunPython(map_payment_methods, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="payment",
            name="payment_method",
            field=models.CharField(
                blank=True,
                choices=[
                    ("cash", "Cash"),
                    ("bank_transfer", "Bank Transfer"),
                    ("check", "Check"),
                    ("gcash", "G-Cash"),
                    ("maya", "Maya"),
                    ("other", "Other"),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
