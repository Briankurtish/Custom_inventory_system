from django.db import models
from apps.workers.models import Worker
from apps.branches.models import Branch

class Customer(models.Model):
    customer_id = models.CharField(
        max_length=50, unique=True, help_text="Code Client"
    )
    customer_name = models.CharField(
        max_length=255, help_text="Noms du client"
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        help_text="Branch associated with the customer"
    )
    postal_code = models.CharField(
        max_length=20, blank=True, null=True, help_text="Code Postal"
    )
    sales_rep = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        limit_choices_to={'role': 'Sales Rep'},  # Only include workers with role "Sales Rep"
        help_text="Assigned Sales Agent"
    )
    contact_person = models.CharField(
        max_length=255, help_text="Contact Person"
    )
    telephone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Telephone"
    )
    email = models.EmailField(
        blank=True, null=True, help_text="Email"
    )
    agreement_number = models.CharField(
        max_length=100, blank=True, null=True, help_text="Numero Agreement (Authorization Number)"
    )
    tax_payer_number = models.CharField(
        max_length=100, blank=True, null=True, help_text="Immatriculation"
    )
    location_plan = models.FileField(upload_to='location_plan/')
    note = models.CharField(
        max_length=100, blank=True, null=True, help_text="Notes"
    )

    def __str__(self):
        return f"{self.customer_id} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.customer_id:
            if self.branch and isinstance(self.branch.branch_id, str):
                # Extract the REG from the branch ID (first 3 letters of branch_id)
                reg = self.branch.branch_id[:3].upper()
            else:
                reg = "UNK"  # Fallback if branch is not set or invalid

            # Get the last customer with the same REG
            last_customer = Customer.objects.filter(customer_id__startswith=f"CUST-{reg}-").order_by('id').last()

            if last_customer:
                # Extract the numerical part from the last customer ID and increment it
                last_number = int(last_customer.customer_id.split('-')[-1])
                new_number = f"{last_number + 1:04d}"
            else:
                # Start from 0001
                new_number = "0001"

            # Construct the customer ID
            self.customer_id = f"CUST-{reg}-{new_number}"

        super().save(*args, **kwargs)
