from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from apps.sms.services import TwilioSMSService
from apps.sms.models import SMSMessage, SMSTemplate, SMSLog
from apps.customers.models import Customer
from apps.workers.models import Worker
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send automated SMS notifications for payments and balances'

    def add_arguments(self, parser):
        parser.add_argument(
            '--payment-reminders',
            action='store_true',
            help='Send payment reminder SMS to customers',
        )
        parser.add_argument(
            '--balance-notifications',
            action='store_true',
            help='Send balance notification SMS to customers',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Send all automated notifications',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        if options['all']:
            options['payment_reminders'] = True
            options['balance_notifications'] = True

        if not any([options['payment_reminders'], options['balance_notifications']]):
            self.stdout.write(
                self.style.WARNING('No notification type specified. Use --help for options.')
            )
            return

        try:
            sms_service = TwilioSMSService()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize SMS service: {str(e)}')
            )
            return

        # Get system user for logging
        try:
            system_user = Worker.objects.filter(role='Director').first()
        except:
            system_user = None

        if options['payment_reminders']:
            self.send_payment_reminders(sms_service, system_user, options['dry_run'])

        if options['balance_notifications']:
            self.send_balance_notifications(sms_service, system_user, options['dry_run'])

    def send_payment_reminders(self, sms_service, system_user, dry_run=False):
        """Send payment reminder SMS to customers with outstanding payments"""
        self.stdout.write('Processing payment reminders...')

        # This is a placeholder - you would need to implement your payment logic
        # For example, get customers with outstanding invoices
        customers_with_payments = Customer.objects.filter(
            # Add your payment criteria here
            # For example: invoices__status='unpaid', invoices__due_date__lte=timezone.now()
        ).distinct()

        if not customers_with_payments.exists():
            self.stdout.write('No customers with outstanding payments found.')
            return

        sent_count = 0
        failed_count = 0

        for customer in customers_with_payments:
            if not customer.telephone:
                continue

            # Get outstanding amount (placeholder logic)
            outstanding_amount = 0  # Replace with actual calculation
            due_date = timezone.now().date() + timedelta(days=7)  # Replace with actual due date

            if dry_run:
                self.stdout.write(
                    f'[DRY RUN] Would send payment reminder to {customer.customer_name} '
                    f'({customer.telephone}) for ${outstanding_amount} due {due_date}'
                )
                continue

            try:
                response = sms_service.send_payment_reminder(
                    customer=customer,
                    amount=outstanding_amount,
                    due_date=due_date,
                    user=system_user
                )

                if response['success']:
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Payment reminder sent to {customer.customer_name}'
                        )
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to send payment reminder to {customer.customer_name}: '
                            f'{response["error"]}'
                        )
                    )

            except Exception as e:
                failed_count += 1
                logger.error(f'Error sending payment reminder to {customer.customer_name}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(
                        f'Error sending payment reminder to {customer.customer_name}: {str(e)}'
                    )
                )

        self.stdout.write(
            f'Payment reminders completed. Sent: {sent_count}, Failed: {failed_count}'
        )

    def send_balance_notifications(self, sms_service, system_user, dry_run=False):
        """Send balance notification SMS to customers"""
        self.stdout.write('Processing balance notifications...')

        # Get customers with phone numbers
        customers = Customer.objects.filter(telephone__isnull=False).exclude(telephone='')

        if not customers.exists():
            self.stdout.write('No customers with phone numbers found.')
            return

        sent_count = 0
        failed_count = 0

        for customer in customers:
            # Get current balance (placeholder logic)
            current_balance = 0  # Replace with actual balance calculation

            if dry_run:
                self.stdout.write(
                    f'[DRY RUN] Would send balance notification to {customer.customer_name} '
                    f'({customer.telephone}) with balance ${current_balance}'
                )
                continue

            try:
                response = sms_service.send_balance_notification(
                    customer=customer,
                    balance=current_balance,
                    user=system_user
                )

                if response['success']:
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Balance notification sent to {customer.customer_name}'
                        )
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to send balance notification to {customer.customer_name}: '
                            f'{response["error"]}'
                        )
                    )

            except Exception as e:
                failed_count += 1
                logger.error(f'Error sending balance notification to {customer.customer_name}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(
                        f'Error sending balance notification to {customer.customer_name}: {str(e)}'
                    )
                )

        self.stdout.write(
            f'Balance notifications completed. Sent: {sent_count}, Failed: {failed_count}'
        )
