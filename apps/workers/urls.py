from django.urls import path
from .views import workerView



urlpatterns = [
    path(
        "workers-list/",
        workerView.as_view(template_name="workers.html"),
        name="workers",
    ),
    path(
        "add-worker/",
        workerView.as_view(template_name="addWorker.html"),
        name="add-workers",
    ),
]
