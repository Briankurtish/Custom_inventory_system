from django.urls import path
from .views import ManagePackView, add_pack_view, edit_pack_view, delete_pack_view, PackSizeAuditLogView


urlpatterns = [
    path(
        "add-pack-size/", add_pack_view, name="add-packsize",
    ),
    path(
        "packsize-logs/", PackSizeAuditLogView, name="packsize-logs",
    ),
    path("edit-pack-size/<int:pk>/", edit_pack_view, name="edit-packsize"),
    path("delete-pack-size/<int:pk>/", delete_pack_view, name="delete-packsize"),
]
