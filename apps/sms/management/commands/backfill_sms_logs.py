from django.core.management.base import BaseCommand
from apps.sms.models import SMSMessage, SMSLog
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create logs for existing SMS messages that don\'t have corresponding logs'

    def handle(self, *args, **options):
        # Get all SMS messages
        all_messages = SMSMessage.objects.all()

        created_logs = 0

        for message in all_messages:
            # Check if there's already a log for this specific message
            existing_log = SMSLog.objects.filter(
                details__icontains=message.recipient_phone,
                timestamp__date=message.created_at.date()
            ).exists()

            if not existing_log:
                # Create a log entry for this message
                SMSLog.objects.create(
                    action='send',
                    details=f'SMS sent to {message.recipient_name} ({message.recipient_phone}) - Status: {message.status}',
                    user=message.sent_by,
                    timestamp=message.created_at,
                    is_error=message.status == 'failed'
                )
                created_logs += 1

        self.stdout.write(
            self.style.SUCCESS(f'Created {created_logs} log entries for existing SMS messages')
        )
