from django.db import models
from django.contrib.auth.models import User
from apps.branches.models import Branch


class EmployeeIDCounter(models.Model):
    prefix = models.CharField(max_length=20, unique=True)
    last_number = models.PositiveIntegerField(default=0)

    @classmethod
    def get_next(cls, prefix):
        # Get or create a counter for the prefix
        counter, created = cls.objects.get_or_create(prefix=prefix)
        counter.last_number += 1
        counter.save()
        return counter.last_number

    @classmethod
    def decrement(cls, prefix):
        try:
            counter = cls.objects.get(prefix=prefix)
            if counter.last_number > 0:
                counter.last_number -= 1
                counter.save()
        except cls.DoesNotExist:
            pass  # No action needed if the counter doesn't exist



class Privilege(models.Model):
    """
    Represents a specific privilege that can be assigned to workers.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Worker(models.Model):
    """
    Worker model representing employees in the system, including roles and privileges.
    """
    ROLE_CHOICES = [
        ('Director', 'Director'),
        ('Pharmacist', 'Pharmacist'),
        ('Human Resource', 'Human Resource'),
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
        User, on_delete=models.CASCADE, related_name='worker_profile'

    )
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='workers'

    )
    department = models.TextField(
        blank=True, null=True
    )
    role = models.CharField(
        max_length=50, choices=ROLE_CHOICES, default='Other'

    )
    employee_id = models.CharField(
        max_length=50, unique=True
    )
    telephone = models.CharField(
        max_length=20, blank=True, null=True
    )

    address = models.TextField(
        blank=True, null=True
    )
    date_joined = models.DateField(
        auto_now_add=True
    )
    privileges = models.ManyToManyField(
        Privilege, blank=True, related_name='workers'

    )

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"

    def save(self, *args, **kwargs):

        is_new = self._state.adding

        if not self.employee_id:
            # Determine the prefix based on role and company
            if self.role == 'Sales Rep':
                company = getattr(self, 'company', None)
                if company == 'GC Pharma':
                    prefix = "GCP-SR"
                elif company == '2A-Promo':
                    prefix = "2AP-SR"
                else:
                    raise ValueError("Invalid company for Sales Rep. Expected 'GC Pharma' or '2A-Promo'.")
            else:
                prefix = "GCP"

            # Get the next number for this prefix
            next_number = EmployeeIDCounter.get_next(prefix)
            self.employee_id = f"{prefix}-{next_number:04d}"

        super().save(*args, **kwargs)

    # Save the worker instance first

        if is_new:
            # Assign default privileges based on role
            default_privileges = {
                'Director': ['Manage Users', 'View Reports', 'Manage Inventory'],
                'Accountant': ['View Reports', 'Manage Finances'],
                'Stock Manager': ['Manage Inventory', 'View Stocks'],
                'Cashier': ['Process Payments'],
                'Sales Rep': ['View Orders', 'Create Orders'],
            }

            # Assign privileges if there are any defaults for this role
            role_privileges = default_privileges.get(self.role, [])
            for privilege_name in role_privileges:
                privilege, created = Privilege.objects.get_or_create(name=privilege_name)
                self.privileges.add(privilege)

    class Meta:
        ordering = ['branch', 'role']
        verbose_name = "Worker"
        verbose_name_plural = "Workers"
