from django.urls import path
from .views import ManageBrandView, add_brand_view, edit_brand_view, delete_brand_view

urlpatterns = [
    path(
        "add-brandName/", add_brand_view, name="add-brandName",
    ),
    path("edit-brand/<int:pk>/", edit_brand_view, name="edit-brand"),
    path("delete-brand/<int:pk>/", delete_brand_view, name="delete-brand"),
]
