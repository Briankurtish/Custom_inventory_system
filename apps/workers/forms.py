from django import forms
from django.contrib.auth.models import User
from .models import RolePrivilege, Worker, Privilege
from apps.branches.models import Branch
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError


class UserCreationForm(forms.ModelForm):

    DEPARTMENT_CHOICES = [
    ('Commercial | Sales & Marketing', 'Commercial | Sales & Marketing'),
    ('Finance', 'Finance'),
    ('Pharmacie | Pharmacy', 'Pharmacie | Pharmacy'),
    ('Ressoure Humaine | Human Resource', 'Ressoure Humaine | Human Resource'),
    # More choices...
]

    MARITAL_STATUS = [
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


    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter first name')}),
        label= _("First Name")
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter last name')}),
        label= _("Last Name")
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Enter email'), 'autocomplete': 'off'}),
        label= _("Email")
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Enter password'), 'autocomplete': 'new-password'}),
        label= _("Password")
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Confirm password')}),
        label= _("Confirm Password")
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label= _("Branch"),
    )
    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Department"),
        required=False,
    )
    role = forms.ChoiceField(
        choices=Worker.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label= _("Role")
    )
    contract_type = forms.ChoiceField(
        required=True,
        choices=CONTRACT_TYPE,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label= _("Contract Type")
    )
    company = forms.ChoiceField(
        choices=COMPANY,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'company'}),
        label= _("Company"),
    )
    manager = forms.ModelChoiceField(
        queryset=Worker.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Manager"),
        help_text=_("Select a manager for this worker"),
    )
    marital_status = forms.ChoiceField(
        choices=MARITAL_STATUS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Marital Status"),

    )

    telephone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter telephone'}),
        label= _("Telephone")
    )


    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
        label= _("Address")
    )
    emergency_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Emegency Contact Name'}),
        label= _("Emergency Contact Name")
    )
    emergency_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Emegency Contact Number'}),
        label= _("Emergency Contact Number")
    )
    recruitment_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'Select Recruitment Date'}),
        label=_("Recruitment Date")
    )

    class Meta:
        model = Worker
        fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password', 'branch', 'department', 'role', 'contract_type', 'company', 'manager', 'marital_status' , 'telephone',  'address', 'emergency_name', 'emergency_phone', 'recruitment_date']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        company = cleaned_data.get("company")
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        if role == 'Sales Rep' and not company:
            self.add_error('company', "Company is required for Sales Rep role.")

        return cleaned_data

    def save(self, commit=True):
        """
        Creates a user and an associated Worker profile.
        """
        cleaned_data = self.cleaned_data

        # Temporarily use the email as a username during User creation
        temporary_username = cleaned_data['email'][:150]  # Truncate to avoid exceeding max length

        # Create the User first
        user = User.objects.create_user(
            username=temporary_username,
            first_name=cleaned_data['first_name'],
            last_name=cleaned_data['last_name'],
            email=cleaned_data['email'],
            password=cleaned_data['password']
        )

        # Create the Worker and generate the employee_id
        worker = Worker(
            user=user,
            role=cleaned_data['role'],
            branch=cleaned_data['branch'],
            telephone=cleaned_data['telephone'],
            department=cleaned_data['department'],
            contract_type=cleaned_data['contract_type'],
            company=cleaned_data['company'],
            manager=cleaned_data['manager'],
            marital_status=cleaned_data['marital_status'],
            emergency_name=cleaned_data['emergency_name'],
            emergency_phone=cleaned_data['emergency_phone'],
            recruitment_date=cleaned_data['recruitment_date'],
            address=cleaned_data['address'],
        )
        worker.company = cleaned_data.get('company')
        worker.save()

        # Update the User's username to match the Worker's employee_id
        user.username = worker.employee_id
        user.save()

        return user, worker


class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = [
            'branch', 'department', 'role', 'contract_type', 'company', 'manager',
            'marital_status', 'emergency_name', 'emergency_phone', 'recruitment_date',
            'telephone', 'address'
        ]
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control', 'placeholder': _('Select department')}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'contract_type': forms.Select(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'manager': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter manager name')}),
            'marital_status': forms.Select(attrs={'class': 'form-control'}),
            'emergency_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter emergency contact name')}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter emergency contact number')}),
            'recruitment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter telephone')}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Enter address')}),
        }
        labels = {
            'branch': _('Branch'),
            'department': _('Department'),
            'role': _('Worker Role'),
            'contract_type': _('Contract Type'),
            'company': _('Company'),
            'manager': _('Manager'),
            'marital_status': _('Marital Status'),
            'emergency_name': _('Emergency Contact Name'),
            'emergency_phone': _('Emergency Contact Phone'),
            'recruitment_date': _('Recruitment Date'),
            'telephone': _('Telephone'),
            'address': _('Address'),
        }


class WorkerProfileForm(forms.ModelForm):
    # Include fields from the User model
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('First Name'),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Last Name'),
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Active'),
    )

    class Meta:
        model = Worker
        fields = ['profile_image','telephone', 'address', 'marital_status', 'emergency_name', 'emergency_phone','is_active']
        widgets = {
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'marital_status': forms.Select(attrs={'class': 'form-control'}),
            'emergency_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter emergency contact name')}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter emergency contact number')}),
        }
        labels = {
            'telephone': _('Telephone'),
            'address': _('Address'),
            'marital_status': _('Marital Status'),
            'emergency_name': _('Emergency Contact Name'),
            'emergency_phone': _('Emergency Contact Phone'),
        }

    def save(self, commit=True):
        """
        Override save method to save both Worker and User data.
        """
        worker = super().save(commit=False)  # Save Worker fields
        user = worker.user  # Access the related User instance

        # Update User fields
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()  # Save User model
            worker.save()  # Save Worker model

        return worker


class WorkerPrivilegeForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['privileges']
        widgets = {
            'privileges': forms.CheckboxSelectMultiple(attrs={'class': 'privileges-list'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sort privileges alphabetically
        self.fields['privileges'].queryset = Privilege.objects.order_by('name')


class PrivilegeForm(forms.ModelForm):
    class Meta:
        model = Privilege
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Privilege Name')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('Privilege Description'), 'rows': 3}),
        }



class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter old password'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}))


class SecurityPinForm(forms.Form):
    pin = forms.CharField(
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter 4-digit PIN'}),
        help_text="Enter a 4-digit security PIN."
    )

    def clean_pin(self):
        pin = self.cleaned_data.get('pin')
        if not pin.isdigit() or len(pin) != 4:
            raise ValidationError("PIN must be a 4-digit number.")
        return pin


class RolePrivilegeForm(forms.ModelForm):
    role = forms.ChoiceField(choices=Worker.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    privileges = forms.ModelMultipleChoiceField(
        queryset=Privilege.objects.all().order_by('name'),  # Order privileges alphabetically
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = RolePrivilege
        fields = ['role', 'privileges']
