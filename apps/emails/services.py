import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import EmailMessage, EmailLog, EmailTemplate
from apps.customers.models import Customer

logger = logging.getLogger(__name__)

class EmailService:
    """Service class for handling email operations"""

    def __init__(self):
        self.smtp_server = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'EMAIL_PORT', 587)
        self.email_host_user = getattr(settings, 'EMAIL_HOST_USER', '')
        self.email_host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gcpharma.com')

    def send_email(self, to_email, subject, message, from_email=None, html_message=None, attachments=None):
        """
        Send a single email message

        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            message (str): Email content (plain text)
            from_email (str): Sender email address (optional)
            html_message (str): HTML version of the message (optional)
            attachments (list): List of file paths to attach (optional)

        Returns:
            dict: Response with success status and details
        """
        try:
            from_email = from_email or self.from_email

            # Create email message
            if html_message:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=[to_email]
                )
                email.attach_alternative(html_message, "text/html")
            else:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=[to_email]
                )

            # Add attachments if provided
            if attachments:
                for attachment_path in attachments:
                    try:
                        with open(attachment_path, 'rb') as file:
                            attachment = MIMEBase('application', 'octet-stream')
                            attachment.set_payload(file.read())
                            encoders.encode_base64(attachment)
                            attachment.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {attachment_path.split("/")[-1]}'
                            )
                            email.attach(attachment)
                    except Exception as e:
                        logger.warning(f"Could not attach file {attachment_path}: {str(e)}")

            # Send email
            email.send()

            return {
                'success': True,
                'message_id': f"email_{timezone.now().timestamp()}",
                'status': 'sent',
                'error': None
            }

        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'status': 'failed',
                'error': str(e)
            }

    def send_bulk_email(self, recipients, subject, message, template=None, user=None, html_message=None):
        """
        Send email to multiple recipients

        Args:
            recipients (list): List of dictionaries with 'email' and 'name' keys
            subject (str): Email subject
            message (str): Email content
            template (EmailTemplate): Optional template used
            user (User): User sending the emails
            html_message (str): HTML version of the message (optional)

        Returns:
            dict: Summary of results
        """
        results = {
            'total': len(recipients),
            'sent': 0,
            'failed': 0,
            'errors': []
        }

        for recipient in recipients:
            try:
                # Send email
                response = self.send_email(
                    to_email=recipient['email'],
                    subject=subject,
                    message=message,
                    html_message=html_message
                )

                # Create email message record
                email_message = EmailMessage.objects.create(
                    recipient_name=recipient.get('name', 'Unknown'),
                    recipient_email=recipient['email'],
                    subject=subject,
                    message=message,
                    template=template,
                    customer=recipient.get('customer'),
                    message_type=template.template_type if template else 'custom',
                    sent_by=user,
                    status='sent' if response['success'] else 'failed',
                    sent_at=timezone.now() if response['success'] else None,
                    error_message=response['error'] if not response['success'] else None
                )

                if response['success']:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'email': recipient['email'],
                        'error': response['error']
                    })

            except Exception as e:
                logger.error(f"Error processing recipient {recipient['email']}: {str(e)}")
                results['failed'] += 1
                results['errors'].append({
                    'email': recipient['email'],
                    'error': str(e)
                })

        # Log the bulk send operation
        EmailLog.objects.create(
            action='bulk_send',
            details=f"Bulk email sent to {results['sent']}/{results['total']} recipients",
            user=user,
            is_error=results['failed'] > 0
        )

        return results

    def send_payment_reminder(self, customer, amount, due_date, user=None):
        """
        Send payment reminder email to a customer

        Args:
            customer (Customer): Customer object
            amount (float): Amount due
            due_date (date): Due date
            user (User): User sending the reminder
        """
        try:
            template = EmailTemplate.objects.filter(
                template_type='payment_reminder',
                is_active=True
            ).first()

            if not template:
                # Create default template if none exists
                template = EmailTemplate.objects.create(
                    name='Default Payment Reminder',
                    subject='Payment Reminder - GC PHARMA',
                    message='Dear {customer_name},\n\nThis is a friendly reminder that your payment of ${amount} is due on {due_date}.\n\nPlease make payment to avoid any inconvenience.\n\nThank you for your business.\n\nBest regards,\nGC PHARMA Team',
                    template_type='payment_reminder',
                    created_by=user
                )

            # Format message with customer data
            message = template.message.format(
                customer_name=customer.customer_name,
                amount=amount,
                due_date=due_date.strftime('%Y-%m-%d')
            )

            # Send email
            response = self.send_email(
                to_email=customer.email if customer.email else customer.telephone,
                subject=template.subject,
                message=message
            )

            # Create email record
            EmailMessage.objects.create(
                recipient_name=customer.customer_name,
                recipient_email=customer.email if customer.email else customer.telephone,
                subject=template.subject,
                message=message,
                template=template,
                customer=customer,
                message_type='payment_reminder',
                sent_by=user,
                status='sent' if response['success'] else 'failed',
                sent_at=timezone.now() if response['success'] else None,
                error_message=response['error'] if not response['success'] else None
            )

            return response

        except Exception as e:
            logger.error(f"Error sending payment reminder: {str(e)}")
            return {'success': False, 'error': str(e)}

    def send_invoice_notification(self, customer, invoice_number, amount, user=None):
        """
        Send invoice notification email to a customer

        Args:
            customer (Customer): Customer object
            invoice_number (str): Invoice number
            amount (float): Invoice amount
            user (User): User sending the notification
        """
        try:
            template = EmailTemplate.objects.filter(
                template_type='invoice_notification',
                is_active=True
            ).first()

            if not template:
                # Create default template if none exists
                template = EmailTemplate.objects.create(
                    name='Default Invoice Notification',
                    subject='New Invoice - GC PHARMA',
                    message='Dear {customer_name},\n\nYour new invoice #{invoice_number} has been generated.\n\nAmount: ${amount}\n\nPlease find the invoice attached.\n\nThank you for your business.\n\nBest regards,\nGC PHARMA Team',
                    template_type='invoice_notification',
                    created_by=user
                )

            # Format message with customer data
            message = template.message.format(
                customer_name=customer.customer_name,
                invoice_number=invoice_number,
                amount=amount
            )

            # Send email
            response = self.send_email(
                to_email=customer.email if customer.email else customer.telephone,
                subject=template.subject,
                message=message
            )

            # Create email record
            EmailMessage.objects.create(
                recipient_name=customer.customer_name,
                recipient_email=customer.email if customer.email else customer.telephone,
                subject=template.subject,
                message=message,
                template=template,
                customer=customer,
                message_type='invoice_notification',
                sent_by=user,
                status='sent' if response['success'] else 'failed',
                sent_at=timezone.now() if response['success'] else None,
                error_message=response['error'] if not response['success'] else None
            )

            return response

        except Exception as e:
            logger.error(f"Error sending invoice notification: {str(e)}")
            return {'success': False, 'error': str(e)}

    def send_welcome_email(self, customer, user=None):
        """
        Send welcome email to a new customer

        Args:
            customer (Customer): Customer object
            user (User): User sending the welcome email
        """
        try:
            template = EmailTemplate.objects.filter(
                template_type='welcome',
                is_active=True
            ).first()

            if not template:
                # Create default template if none exists
                template = EmailTemplate.objects.create(
                    name='Default Welcome Email',
                    subject='Welcome to GC PHARMA',
                    message='Dear {customer_name},\n\nWelcome to GC PHARMA! We are excited to have you as our valued customer.\n\nWe look forward to serving you with the best pharmaceutical products and services.\n\nIf you have any questions, please don\'t hesitate to contact us.\n\nBest regards,\nGC PHARMA Team',
                    template_type='welcome',
                    created_by=user
                )

            # Format message with customer data
            message = template.message.format(
                customer_name=customer.customer_name
            )

            # Send email
            response = self.send_email(
                to_email=customer.email if customer.email else customer.telephone,
                subject=template.subject,
                message=message
            )

            # Create email record
            EmailMessage.objects.create(
                recipient_name=customer.customer_name,
                recipient_email=customer.email if customer.email else customer.telephone,
                subject=template.subject,
                message=message,
                template=template,
                customer=customer,
                message_type='welcome',
                sent_by=user,
                status='sent' if response['success'] else 'failed',
                sent_at=timezone.now() if response['success'] else None,
                error_message=response['error'] if not response['success'] else None
            )

            return response

        except Exception as e:
            logger.error(f"Error sending welcome email: {str(e)}")
            return {'success': False, 'error': str(e)}
