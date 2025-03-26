from django.urls import path
from .views import ManageGenericView, add_generic_name_view, edit_generic_view, delete_generic_view, GenericAuditLogView


urlpatterns = [
    path(
        "add-genericName/", add_generic_name_view, name="add-genericName",
    ),
    path(
        "generic-logs/", GenericAuditLogView, name="generic-logs",
    ),
    path("edit-generic/<int:pk>/", edit_generic_view, name="edit-genericName"),
    path("delete-generic/<int:pk>/", delete_generic_view, name="delete-genericName"),
]
