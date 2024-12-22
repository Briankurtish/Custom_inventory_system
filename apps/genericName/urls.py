from django.urls import path
from .views import ManageGenericView, add_generic_name, edit_generic_view, delete_generic_view


urlpatterns = [
    path(
        "add-genericName/", add_generic_name, name="add-genericName",
    ),
    path("edit-generic/<int:pk>/", edit_generic_view, name="edit-genericName"),
    path("delete-generic/<int:pk>/", delete_generic_view, name="delete-genericName"),
]
