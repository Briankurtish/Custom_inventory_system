from django.urls import path
from .views import *



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
    path("edit-privilege/<int:privilege_id>/", edit_privilege, name="edit_privilege"),
    path('privileges/', get_roles_and_privileges, name='privileges'),

    path('change-password/', password_change_view, name='password_change'),
    path('worker/toggle-status/<int:pk>/', toggle_worker_status, name='toggle_worker_status'),
    path('worker/<int:user_id>/change-password/', change_worker_password, name='change-worker-password'),

    path('online-workers/', OnlineWorkersView, name='online-workers'),

    path('create-pin/', create_security_pin, name='create_security_pin'),
    path('update-pin/', update_security_pin, name='update_security_pin'),

    path('validate-password/', validate_password, name='validate_password'),

    path("validate-security-pin/", validate_security_pin, name="validate_security_pin"),

    path('assign-privileges/', assign_privileges_to_role, name='assign_privileges'),

    path("check_security_pin/", check_security_pin, name="check_security_pin"),

]
