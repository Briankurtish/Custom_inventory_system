from django.urls import path
from .views import ManageGenericView, add_generic_view, edit_generic_view


urlpatterns = [
    path(
        "add-genericName/", add_generic_view, name="add-genericName",
    ),
    path("edit-generic/<int:pk>/", edit_generic_view, name="edit-genericName"),
    # path("delete-branch/<int:pk>/", delete_branch_view, name="delete-branch"),
]
