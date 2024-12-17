from django.db import models
from django.contrib.auth.models import User
from apps.branches.models import Branch

class Privilege(models.Model):
    """
    Represents a specific privilege that can be assigned to workers.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Name of the privilege")
    description = models.TextField(blank=True, null=True, help_text="Description of the privilege")

    def __str__(self):
        return self.name

class Worker(models.Model):
    """
    Worker model representing employees in the system, including roles and privileges.
    """
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
    privileges = models.ManyToManyField(
        Privilege, blank=True, related_name='workers',
        help_text="Privileges assigned to the worker"
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
        
        """
        Automatically assign default privileges based on the worker's role.
        """
        is_new = self._state.adding  # Check if the instance is being created
        super().save(*args, **kwargs)  # Save the worker instance first

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
