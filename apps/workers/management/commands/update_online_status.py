# management/commands/update_online_status.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from your_app.models import Worker
from datetime import timedelta

class Command(BaseCommand):
    help = 'Update online status of workers based on last activity'

    def handle(self, *args, **options):
        # Consider a user as offline if they haven't been active for the last 5 minutes
        offline_threshold = timezone.now() - timedelta(minutes=5)
        
        # Set users as offline if their last activity is older than the threshold
        Worker.objects.filter(last_active__lt=offline_threshold).update(is_online=False)
        
        self.stdout.write(self.style.SUCCESS('Successfully updated online status'))