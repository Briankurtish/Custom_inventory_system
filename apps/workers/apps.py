from django.apps import AppConfig

class WorkersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workers'

    def ready(self):
        # Import signals when the app is ready
        import apps.workers.signals
