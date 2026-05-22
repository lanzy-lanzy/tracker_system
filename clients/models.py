from django.db import models


class Client(models.Model):
    client_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.client_name

    @property
    def total_outstanding(self):
        from payments.models import Payment
        payments = Payment.objects.filter(client=self)
        total = 0
        for p in payments:
            total += p.balance
        return total
