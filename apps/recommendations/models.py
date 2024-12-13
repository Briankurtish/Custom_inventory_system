from django.db import models
from apps.workers.models import Worker
from apps.products.models import Product

class Recommendation(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    pharmacist = models.ForeignKey(
        Worker, on_delete=models.CASCADE, related_name='recommendations',
        help_text="The pharmacist making the recommendation. Must be assigned the Pharmacist role."
    )
    product = models.CharField(
        max_length=255, help_text="Product"
    )
    quantity = models.PositiveIntegerField(
        help_text="Recommended quantity for the next shipment."
    )
    reason = models.TextField(
         help_text="Optional reason for the recommendation."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Current status of the recommendation."
    )
    date_created = models.DateTimeField(
        auto_now_add=True, help_text="The date and time the recommendation was created."
    )
    recommendation_document = models.FileField(
    upload_to='recommendation_document/',
    help_text="Upload a recommendation document (required)."
)

    def __str__(self):
        return f"Recommendation by {self.pharmacist.user.get_full_name()} for {self.product.name} ({self.status})"

    class Meta:
        ordering = ['-date_created']
        verbose_name = "Recommendation"
        verbose_name_plural = "Recommendations"
