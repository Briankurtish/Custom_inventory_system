from django.db import models
from apps.workers.models import Worker
from apps.branches.models import Branch
from datetime import datetime

class Customer(models.Model):
    customer_id = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=255)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        related_name='customers'
    )
    postal_code = models.CharField(max_length=50, null=True)
    sales_rep = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        limit_choices_to={'role': 'Sales Rep'}
    )
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=20, null=True)
    email = models.EmailField(blank=True, null=True)
    agreement_number = models.CharField(max_length=100, blank=True, null=True)
    tax_payer_number = models.CharField(max_length=100, blank=True, null=True)
    location_plan = models.FileField(upload_to='location_plan/', blank=True, null=True)
    note = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now)
    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_by_worker'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['customer_name', 'postal_code'],
                name='unique_customer_name_and_postal_code'
            )
        ]

    def __str__(self):
        return f"{self.customer_id} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.customer_id:
            reg = self.branch.branch_id[:3].upper() if self.branch else "UNK"
            last_customer = Customer.objects.filter(
                customer_id__startswith=f"CUST-{reg}-"
            ).order_by('id').last()
            new_number = f"{(int(last_customer.customer_id.split('-')[-1]) + 1) if last_customer else 1:04d}"
            self.customer_id = f"CUST-{reg}-{new_number}"

        super().save(*args, **kwargs)


class CustomerAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
    ]

    user = models.ForeignKey(
        'workers.Worker', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='customer_log_created'
    )
    customer_name = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # To store extra details (e.g., changes)

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.customer_name} on {self.timestamp}"
