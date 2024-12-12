from django.urls import path
from .views import delete_batch_view, delete_product_view, update_product_view, add_product_view, ManageProductView, add_batch_view, edit_batch_view



urlpatterns = [
    
    path(
        "add-batch/", add_batch_view, name="add-batch",
    ),
    path(
        "product-list/", ManageProductView, name="products",
    ),
    path(
        "add-product/", add_product_view, name="add-product",
    ),
     path("edit-batch/<int:pk>/", edit_batch_view, name="edit-batch"),  # Edit route

    path("edit-product/<int:pk>/", update_product_view, name="edit-product"),
    path("delete-product/<int:pk>/", delete_product_view, name="delete-product"),

    path("delete-batch/<int:pk>/", delete_batch_view, name="delete-batch"),
]
