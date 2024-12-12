from django.contrib import admin
from .models import Batch

# Register your models here.
@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'expiry_date')
    search_fields = ('batch_number',)