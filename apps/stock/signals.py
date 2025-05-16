from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Stock

@receiver(pre_save, sender=Stock)
def update_total_stock(sender, instance, **kwargs):
    """
    Signal to update total_stock before saving a Stock instance.
    Ensures stock quantities are updated dynamically whenever Stock is modified.
    """
    # Set fixed_beginning_inventory only once (if it's not already set)
    if instance.fixed_beginning_inventory is None:
        instance.fixed_beginning_inventory = instance.begining_inventory or 0

    # Ensure beginning_inventory always matches fixed_beginning_inventory
    instance.begining_inventory = instance.fixed_beginning_inventory

    # Compute total inventory
    instance.total_inventory = (instance.fixed_beginning_inventory or 0) + instance.quantity

    # Compute available stock after transfers
    instance.total_stock = instance.total_inventory - (instance.quantity_transferred + instance.total_sold + instance.samples_quantity + instance.damaged_quantity + instance.sickness_quantity)
