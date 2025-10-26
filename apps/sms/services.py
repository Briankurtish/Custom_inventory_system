import logging
from django.conf import settings
from django.utils import timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from .models import SMSMessage, SMSLog, SMSTemplate
from apps.customers.models import Customer

logger = logging.getLogger(__name__)

class TwilioSMSService:
    """Service class for handling SMS operations with Twilio"""

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER

        if not all([self.account_sid, self.auth_token, self.phone_number]):
            raise ValueError("Twilio credentials not properly configured")

        self.client = Client(self.account_sid, self.auth_token)

    def send_sms(self, to_phone, message, from_phone=None):
        """
        Send a single SMS message

        Args:
            to_phone (str): Recipient phone number
            message (str): Message content
            from_phone (str): Sender phone number or sender ID (optional)

        Returns:
            dict: Response with success status and details
        """
        try:
            from_phone = from_phone or self.phone_number

            # Format phone number (ensure it starts with +)
            if not to_phone.startswith('+'):
                to_phone = '+' + to_phone.lstrip('+')

            logger.info(f"Attempting to send SMS to {to_phone} from {from_phone}")

            # Check if from_phone is a sender ID (alphanumeric) or phone number
            if from_phone.startswith('+') or from_phone.isdigit():
                # It's a phone number
                message_obj = self.client.messages.create(
                    body=message,
                    from_=from_phone,
                    to=to_phone
                )
            else:
                # It's a sender ID (alphanumeric)
                message_obj = self.client.messages.create(
                    body=message,
                    from_=from_phone,
                    to=to_phone
                )

            logger.info(f"SMS sent successfully. SID: {message_obj.sid}, Status: {message_obj.status}")

            return {
                'success': True,
                'sid': message_obj.sid,
                'status': message_obj.status,
                'error': None
            }

        except TwilioException as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return {
                'success': False,
                'sid': None,
                'status': 'failed',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected SMS error: {str(e)}")
            return {
                'success': False,
                'sid': None,
                'status': 'failed',
                'error': str(e)
            }

    def send_bulk_sms(self, recipients, message, template=None, user=None):
        """
        Send SMS to multiple recipients

        Args:
            recipients (list): List of dictionaries with 'phone' and 'name' keys
            message (str): Message content
            template (SMSTemplate): Optional template used
            user (Worker): User sending the messages

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
                # Send SMS
                response = self.send_sms(recipient['phone'], message)

                # Create SMS message record
                sms_message = SMSMessage.objects.create(
                    recipient_name=recipient.get('name', 'Unknown'),
                    recipient_phone=recipient['phone'],
                    message=message,
                    template=template,
                    customer=recipient.get('customer'),
                    message_type=template.template_type if template else 'custom',
                    sent_by=user,
                    twilio_sid=response['sid'] if response['success'] else None,
                    twilio_status=response['status'],
                    status='sent' if response['success'] else 'failed',
                    sent_at=timezone.now() if response['success'] else None,
                    error_message=response['error'] if not response['success'] else None
                )

                if response['success']:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'phone': recipient['phone'],
                        'error': response['error']
                    })

            except Exception as e:
                logger.error(f"Error processing recipient {recipient['phone']}: {str(e)}")
                results['failed'] += 1
                results['errors'].append({
                    'phone': recipient['phone'],
                    'error': str(e)
                })

        # Log the bulk send operation
        SMSLog.objects.create(
            action='bulk_send',
            details=f"Bulk SMS sent to {results['sent']}/{results['total']} recipients",
            user=user,
            is_error=results['failed'] > 0
        )

        return results

    def send_payment_reminder(self, customer, amount, due_date, user=None):
        """
        Send payment reminder SMS to a customer

        Args:
            customer (Customer): Customer object
            amount (float): Amount due
            due_date (date): Due date
            user (Worker): User sending the reminder
        """
        try:
            template = SMSTemplate.objects.filter(
                template_type='payment_reminder',
                is_active=True
            ).first()

            if not template:
                # Create default template if none exists
                template = SMSTemplate.objects.create(
                    name='Default Payment Reminder',
                    subject='Payment Reminder',
                    message='Dear {customer_name}, your payment of ${amount} is due on {due_date}. Please make payment to avoid any inconvenience.',
                    template_type='payment_reminder',
                    created_by=user
                )

            # Format message with customer data
            message = template.message.format(
                customer_name=customer.customer_name,
                amount=amount,
                due_date=due_date.strftime('%Y-%m-%d')
            )

            # Send SMS
            response = self.send_sms(customer.telephone, message)

            # Create SMS record
            SMSMessage.objects.create(
                recipient_name=customer.customer_name,
                recipient_phone=customer.telephone,
                subject=template.subject,
                message=message,
                template=template,
                customer=customer,
                message_type='payment_reminder',
                sent_by=user,
                twilio_sid=response['sid'] if response['success'] else None,
                twilio_status=response['status'],
                status='sent' if response['success'] else 'failed',
                sent_at=timezone.now() if response['success'] else None,
                error_message=response['error'] if not response['success'] else None
            )

            return response

        except Exception as e:
            logger.error(f"Error sending payment reminder: {str(e)}")
            return {'success': False, 'error': str(e)}

    def send_balance_notification(self, customer, balance, user=None):
        """
        Send balance notification SMS to a customer

        Args:
            customer (Customer): Customer object
            balance (float): Current balance
            user (Worker): User sending the notification
        """
        try:
            template = SMSTemplate.objects.filter(
                template_type='balance_notification',
                is_active=True
            ).first()

            if not template:
                # Create default template if none exists
                template = SMSTemplate.objects.create(
                    name='Default Balance Notification',
                    subject='Account Balance Update',
                    message='Dear {customer_name}, your current account balance is ${balance}. Thank you for your business.',
                    template_type='balance_notification',
                    created_by=user
                )

            # Format message with customer data
            message = template.message.format(
                customer_name=customer.customer_name,
                balance=balance
            )

            # Send SMS
            response = self.send_sms(customer.telephone, message)

            # Create SMS record
            SMSMessage.objects.create(
                recipient_name=customer.customer_name,
                recipient_phone=customer.telephone,
                subject=template.subject,
                message=message,
                template=template,
                customer=customer,
                message_type='balance_notification',
                sent_by=user,
                twilio_sid=response['sid'] if response['success'] else None,
                twilio_status=response['status'],
                status='sent' if response['success'] else 'failed',
                sent_at=timezone.now() if response['success'] else None,
                error_message=response['error'] if not response['success'] else None
            )

            return response

        except Exception as e:
            logger.error(f"Error sending balance notification: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_message_status(self, sms_message):
        """
        Get the current status of a sent SMS message

        Args:
            sms_message (SMSMessage): SMS message object

        Returns:
            dict: Updated status information
        """
        try:
            if not sms_message.twilio_sid:
                return {'success': False, 'error': 'No Twilio SID available'}

            message = self.client.messages(sms_message.twilio_sid).fetch()

            # Update the message status
            sms_message.twilio_status = message.status
            if message.status == 'delivered':
                sms_message.status = 'delivered'
                sms_message.delivered_at = timezone.now()
            elif message.status in ['failed', 'undelivered']:
                sms_message.status = 'failed'

            sms_message.save()

            return {
                'success': True,
                'status': message.status,
                'error': None
            }

        except TwilioException as e:
            logger.error(f"Error fetching message status: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error fetching message status: {str(e)}")
            return {'success': False, 'error': str(e)}
