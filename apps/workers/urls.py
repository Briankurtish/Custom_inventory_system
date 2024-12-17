from django.urls import path
from .views import ManageWorkerView, add_worker_view, update_worker_view, manage_worker_privileges, create_privilege



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
    path('workers/<int:worker_id>/manage-privileges/', manage_worker_privileges, name='manage_worker_privileges'),
    path('create-privilege/', create_privilege, name='create_privilege'),
]
