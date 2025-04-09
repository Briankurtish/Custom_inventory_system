from django.utils import timezone
from apps.workers.models import Worker

class UpdateLastActiveMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Update last_active for authenticated workers on each request
        if request.user.is_authenticated:
            try:
                worker = request.user.worker_profile
                worker.last_active = timezone.now()
                worker.save()
            except Worker.DoesNotExist:
                pass

        response = self.get_response(request)
        return response