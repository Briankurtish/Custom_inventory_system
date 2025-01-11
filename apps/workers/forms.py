from django import forms
from django.contrib.auth.models import User
from .models import Worker, Privilege
from apps.branches.models import Branch
from django.utils.translation import gettext_lazy as _


class UserCreationForm(forms.ModelForm):
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
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Enter email')}),
        label= _("Email")
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Enter password')}),
        label= _("Password")
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Confirm password')}),
        label= _("Confirm Password")
    )
    role = forms.ChoiceField(
        choices=Worker.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label= _("Role")
    )
    company = forms.ChoiceField(
        choices=[('GC Pharma', 'GC Pharma'), ('2A-Promo', '2A-Promo')],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'company'}),
        label= _("Company"),
        required=False
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label= _("Branch"),
    )
    telephone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter telephone'}),
        label= _("Telephone")
    )
    department = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter department'}),
        label= _("Department")
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
        label= _("Address")
    )

    class Meta:
        model = Worker
        fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password', 'role', 'branch', 'telephone', 'department', 'address']

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
            address=cleaned_data['address']
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
        fields = ['role', 'branch', 'telephone', 'department', 'address']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter telephone'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter department'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
        }
        labels = {
            'role': _('Worker Role'),
            'branch': _('Branch'),
            'telephone': _('Telephone'),
            'department': _('Department'),
            'address': _('Address'),
        }
        
        
class WorkerPrivilegeForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['privileges']  # Only include privileges field
        widgets = {
            'privileges': forms.CheckboxSelectMultiple(attrs={'class': 'privileges-list'})
        }
        

class PrivilegeForm(forms.ModelForm):
    class Meta:
        model = Privilege
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Privilege Name')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('Privilege Description'), 'rows': 3}),
        }