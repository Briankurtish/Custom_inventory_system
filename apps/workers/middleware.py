# middleware.py
from django.utils import timezone
from .models import Worker

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            try:
                worker = Worker.objects.get(user=request.user)
                worker.last_active = timezone.now()
                worker.save()
            except Worker.DoesNotExist:
                pass
        return response