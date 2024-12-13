from django.db import models


# Create your models here.

class Customer(models.Model):
    customer_id = models.CharField(
        max_length=50, unique=True, help_text="Code Client"
    )
    customer_name = models.CharField(
        max_length=255, help_text="Noms du client"
    )
    postal_code = models.CharField(
        max_length=20, blank=True, null=True, help_text="Code Postal"
    )
    sales_rep = models.ForeignKey(
    'sales_rep.SalesAgent', on_delete=models.SET_NULL, null=True, blank=True, related_name='customers',
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
            last_customer = Customer.objects.order_by('id').last()
            if last_customer and last_customer.customer_id.startswith("GCL"):
                last_number = int(last_customer.customer_id[3:])  # Extract the number part
                self.customer_id = f"GCL{last_number + 1:04d}"  # Increment and pad with zeros
            else:
                self.customer_id = "GCL0001"  # Start from GCL0001
        super().save(*args, **kwargs)