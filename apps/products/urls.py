from django.urls import path
from .views import delete_batch_view, delete_product_view, update_product_view, add_product_view, ManageProductView, add_batch_view, edit_batch_view, get_brand_name, edit_product_view, fetch_brand_names


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

    path("edit-product/<int:pk>/", edit_product_view, name="edit-product"),
    path("edit-price/<int:pk>/", update_product_view, name="edit-price"),
    path("delete-product/<int:pk>/", delete_product_view, name="delete-product"),

    path("delete-batch/<int:pk>/", delete_batch_view, name="delete-batch"),
    
    path('get-brand-name/<int:generic_name_id>/', get_brand_name, name='get-brand-name'),
    
    path('fetch-brand-names/', fetch_brand_names, name='fetch_brand_names'),
    
]
