from django.db import models
from django.contrib.auth.models import User
from apps.branches.models import Branch
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password


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
    
    CATEGORY_CHOICES = [
        ('Inventory Management', 'Inventory Management'),
        ('Human Resource', 'Human Resource'),
        ('Order and Sales', 'Order and sales'),
        ('Finance', 'Finance'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.TextField(choices=CATEGORY_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.name

class Worker(models.Model):
    """
    Worker model representing employees in the system, including roles, privileges, and a 4-digit security PIN.
    """
    ROLE_CHOICES = [
        ('Director General', 'Director General'),
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

    MARITAL_STATUS_CHOICES = [
        ('Married', 'Married'),
        ('Single', 'Single'),
        ('Divorced', 'Divorced'),
        ('Widow', 'Widow'),
        ('Widower', 'Widower'),
    ]

    COMPANY = [
        ('GC Pharma', 'GC Pharma'),
        ('2A-Promo', '2A-Promo'),
    ]

    CONTRACT_TYPE = [
        ('Contrat à Durée Indéterminée (CDI)/Permanent Contract', 'Contrat à Durée Indéterminée (CDI)/Permanent Contract'),
        ('Contrat à durée déterminée ( CDD) /Fixed-term Contract', 'Contrat à durée déterminée ( CDD) /Fixed-term Contract'),
        ("Contrat d’essai / Trial contract", "Contrat d’essai / Trial contract"),
    ]

    DEPARTMENT_CHOICES = [
        ('Commercial | Sales & Marketing', 'Commercial | Sales & Marketing'),
        ('Finance', 'Finance'),
        ('Pharmacie | Pharmacy', 'Pharmacie | Pharmacy'),
        ('Ressoure Humaine | Human Resource', 'Ressoure Humaine | Human Resource'),
        # More choices...
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='worker_profile'
    )
    employee_id = models.CharField(
        max_length=50, unique=True
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, related_name='workers'
    )
    department = models.CharField(
        choices=DEPARTMENT_CHOICES,
        blank=True, null=True
    )
    role = models.CharField(
        max_length=50, choices=ROLE_CHOICES, default='Other'
    )
    contract_type = models.CharField(
        choices=CONTRACT_TYPE,
        blank=True, null=True
    )
    company = models.CharField(
        choices=COMPANY,
        blank=True, null=True
    )
    manager = models.TextField(
        blank=True, null=True
    )
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        blank=True,
        null=True,
    )
    telephone = models.CharField(
        max_length=20, blank=True, null=True
    )
    address = models.TextField(
        blank=True, null=True
    )
    emergency_name = models.TextField(
        blank=True, null=True
    )
    emergency_phone = models.TextField(
        blank=True, null=True
    )
    date_joined = models.DateField(
        auto_now_add=True
    )
    recruitment_date = models.DateField(
        blank=True, null=True
    )
    privileges = models.ManyToManyField(
        'Privilege', blank=True, related_name='workers'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Indicates whether the worker can log in."
    )
    is_online = models.BooleanField(
        default=False,
        verbose_name="Online Status",
        help_text="Indicates whether the worker is currently online."
    )
    last_active = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='worker_created'
    )
    profile_image = models.ImageField(default='avatar.jpg', upload_to='Profile_Images')
    security_pin = models.CharField(
        max_length=128,  # Store the hashed PIN
        blank=True,
        null=True,
        help_text="A 4-digit security PIN for extra security."
    )

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"

    def clean(self):
        """
        Validate fields before saving the model.
        """
        super().clean()
        if self.role == 'Sales Rep' and not self.company:
            raise ValidationError("Company is required for Sales Rep.")

        # Validate security_pin if it is being set
        if self.security_pin and (len(self.security_pin) != 4 or not self.security_pin.isdigit()):
            raise ValidationError("Security PIN must be a 4-digit number.")

    def save(self, *args, **kwargs):
        """
        Custom save method to sync Worker and User is_active status,
        assign default privileges for new workers, and hash the security PIN.
        """
        is_new = self._state.adding

        # Generate employee_id if not set
        if not self.employee_id:
            prefix = self.get_employee_id_prefix()
            next_number = EmployeeIDCounter.get_next(prefix)
            self.employee_id = f"{prefix}-{next_number:04d}"

        # Sync is_active status with related User
        if self.user:
            self.user.is_active = self.is_active
            self.user.save()

        # Hash the security_pin if it is being set
        if self.security_pin and len(self.security_pin) == 4 and self.security_pin.isdigit():
            self.security_pin = make_password(self.security_pin)

        super().save(*args, **kwargs)

        # Assign default privileges for new workers
        if is_new:
            self.assign_default_privileges()

    def get_employee_id_prefix(self):
        """
        Determine the employee ID prefix based on role and company.
        """
        if self.role == 'Sales Rep':
            if self.company == 'GC Pharma':
                return "GCP-SR"
            elif self.company == '2A-Promo':
                return "2AP-SR"
            else:
                raise ValueError("Invalid company for Sales Rep.")
        return "GCP"


    def assign_default_privileges(self):
        """
        Assign default privileges based on role from RolePrivilege model.
        """
        try:
            role_privilege = RolePrivilege.objects.get(role=self.role)
            self.privileges.set(role_privilege.privileges.all())
        except RolePrivilege.DoesNotExist:
            pass  # No default privileges for this role
        """
        Assign default privileges based on role.

        """
        # default_privileges = {
        #     'Director': ['Manage Users', 'View Reports', 'Manage Inventory'],
        #     'Accountant': ['View Reports', 'Manage Finances'],
        #     'Stock Manager': ['Manage Inventory', 'View Stocks'],
        #     'Cashier': ['Process Payments'],
        #     'Sales Rep': ['View Orders', 'Create Orders'],
        # }
        # role_privileges = default_privileges.get(self.role, [])
        # for privilege_name in role_privileges:
        #     privilege, _ = Privilege.objects.get_or_create(name=privilege_name)
        #     self.privileges.add(privilege)

    def set_security_pin(self, raw_pin):
        """
        Set the security PIN after hashing it.
        """
        if len(raw_pin) != 4 or not raw_pin.isdigit():
            raise ValidationError("Security PIN must be a 4-digit number.")
        self.security_pin = make_password(raw_pin)

    def check_security_pin(self, raw_pin):
        """
        Validate the provided PIN against the stored hashed PIN.
        """
        if not self.security_pin:
            return False
        return check_password(raw_pin, self.security_pin)

    class Meta:
        ordering = ['branch', 'role']
        verbose_name = "Worker"
        verbose_name_plural = "Workers"



class RolePrivilege(models.Model):
    role = models.CharField(max_length=50, choices=Worker.ROLE_CHOICES, unique=True)
    privileges = models.ManyToManyField(Privilege, related_name='role_privileges')

    def __str__(self):
        return f"{self.role}"
