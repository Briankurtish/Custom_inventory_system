from django.urls import path
from .views import ManageWorkerView, add_worker_view, update_worker_view



urlpatterns = [
    path(
        "workers-list/",
        ManageWorkerView,
        name="workers",
    ),
    path(
        "add-worker/",
        add_worker_view,
        name="add-workers",
    ),
    path("edit-worker/<int:pk>/", update_worker_view, name="edit-worker"),
]
