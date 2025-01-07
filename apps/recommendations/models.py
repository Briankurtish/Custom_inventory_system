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
    )
    product = models.CharField(
        max_length=255,
    )
    quantity = models.PositiveIntegerField(
    )
    reason = models.TextField(
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
    )
    date_created = models.DateTimeField(
        auto_now_add=True, 
    )
    recommendation_document = models.FileField(
    upload_to='recommendation_document/',
)

    def __str__(self):
        return f"Recommendation by {self.pharmacist.user.get_full_name()} for {self.product.name} ({self.status})"

    class Meta:
        ordering = ['-date_created']
        verbose_name = "Recommendation"
        verbose_name_plural = "Recommendations"
