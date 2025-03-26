from django.urls import path
from .views import ManageWorkerView, add_worker_view, edit_worker_profile_view, update_worker_view, manage_worker_privileges, create_privilege, get_roles_and_privileges, delete_worker_view, password_change_view



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
    path("delete-worker/<int:pk>/", delete_worker_view, name="delete-worker"),
    path('worker/edit/<int:pk>/', edit_worker_profile_view, name='edit_worker_profile'),
    path('workers/<int:worker_id>/manage-privileges/', manage_worker_privileges, name='manage_worker_privileges'),
    path('create-privilege/', create_privilege, name='create_privilege'),
    path('privileges/', get_roles_and_privileges, name='privileges'),

    path('change-password/', password_change_view, name='password_change'),
]
