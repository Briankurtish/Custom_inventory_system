from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Worker, Privilege
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out

@receiver(post_save, sender=Worker)
def assign_default_privileges(sender, instance, created, **kwargs):
    """
    Signal to assign default privileges to a worker after creation and send a welcome email.
    """
    if created:  # Only when a new Worker is created
        # Assign default privileges based on the role
        default_privileges = {
            'Director': ['Manage Users', 'View Reports', 'Manage Inventory'],
            'Marketing Director': ['View Stocks', 'Request Stock'],
            'Pharmacist': ['Recommend Medical Products', 'Prepare Customs Clearing Report', 'Creates Good Receipt Note', 'Accept or Decline Stock Requisition'],
            'Accountant': ['View Reports', 'Manage Finances'],
            'Central Stock Manager': ['Manage Inventory', 'View Stocks', "View Products", "View Approved Requests", 'Transfer Stock'],
            'Stock Manager': ['Manage Inventory', 'View Stocks', 'View Stock In Transit'],
            'Cashier': ['Process Payments'],
            'Sales Rep': ['View Orders', 'Create Orders'],
        }

        role_privileges = default_privileges.get(instance.role, [])
        for privilege_name in role_privileges:
            privilege, _ = Privilege.objects.get_or_create(name=privilege_name)
            instance.privileges.add(privilege)

        # Send the welcome email to the newly created worker
        try:
            subject = "Welcome to GC Pharma Inventory Management System"
            message = (
                f"Hello {instance.employee_id},\n\n"
                "Your account has been created successfully. Below are your login credentials:\n\n"
                f"Username: {instance.employee_id}\n"
                "Password: Password2023#\n\n"
                "Please log in to your account via the link below and update your details if necessary.\n\n"
                "https://pharmamgtsystemgc.com/"
            )

            # Correct way to set the sender with a name
            from_email = "GC PHARMA <admin@pharmamgtsystemgc.com>"

            # Send the email
            recipient_list = [instance.user.email]
            send_mail(subject, message, from_email, recipient_list)

        except Exception as e:
            print(f"Error sending email: {e}")


@receiver(user_logged_in)
def set_worker_online(sender, user, request, **kwargs):
    """
    Set the worker's is_online to True and update last_active on login.
    """
    try:
        worker = user.worker_profile
        worker.is_online = True
        worker.last_active = timezone.now()
        worker.save()
    except Worker.DoesNotExist:
        pass

@receiver(user_logged_out)
def set_worker_offline(sender, user, request, **kwargs):
    """
    Set the worker's is_online to False on logout.
    """
    try:
        worker = user.worker_profile
        worker.is_online = False
        worker.save()
    except Worker.DoesNotExist:
        pass
