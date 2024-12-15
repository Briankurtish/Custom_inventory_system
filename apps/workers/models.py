from django.db import models
from django.contrib.auth.models import User
from apps.branches.models import Branch

class Worker(models.Model):
    ROLE_CHOICES = [
        ('Director', 'Director'),
        ('Pharmacist', 'Pharmacist'),
        ('Marketing Director', 'Marketing Director'),
        ('Central Stock Manager', 'Central Stock Manager'),
        ('Stock Manager', 'Stock Manager'),
        ('Central Stock Keeper', 'Central Stock Keeper'),
        ('Stock Keeper', 'Stock Keeper'),
        ('Accountant', 'Accountant'),
        ('Cashier', 'Cashier'),
        ('Secretary', 'Secretary'),
        ('Sales Rep', 'Sales Rep'),
        ('Driver', 'Driver'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='worker_profile',
        help_text="Associated user account for the worker"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='workers',
        help_text="Branch the worker belongs to"
    )
    role = models.CharField(
        max_length=50, choices=ROLE_CHOICES, default='Other',
        help_text="Role of the worker in the organization"
    )
    employee_id = models.CharField(
        max_length=50, unique=True, help_text="Unique identifier for the worker"
    )
    telephone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Telephone number of the worker"
    )
    department = models.TextField(
        blank=True, null=True, help_text="Department of the worker"
    )
    address = models.TextField(
        blank=True, null=True, help_text="Address of the worker"
    )
    date_joined = models.DateField(
        auto_now_add=True, help_text="Date when the worker joined"
    )

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            if self.role == 'Sales Rep':
                # Generate an ID for Sales Reps starting with "2AP-"
                last_worker = Worker.objects.filter(employee_id__startswith="2AP-").order_by('id').last()
                if last_worker:
                    last_number = int(last_worker.employee_id[4:])  # Extract digits after "2AP-"
                    self.employee_id = f"2AP-{last_number + 1:03d}"
                else:
                    self.employee_id = "2AP-001"
            else:
                # Generate a generic ID starting with "GC-W"
                last_worker = Worker.objects.filter(employee_id__startswith="GC-W").order_by('id').last()
                if last_worker:
                    last_number = int(last_worker.employee_id[5:])  # Extract digits after "GC-W"
                    self.employee_id = f"GC-W{last_number + 1:04d}"
                else:
                    self.employee_id = "GC-W0001"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['branch', 'role']
        verbose_name = "Worker"
        verbose_name_plural = "Workers"
