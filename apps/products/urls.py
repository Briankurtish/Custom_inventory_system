from django.urls import path
from .views import productView



urlpatterns = [
    path(
        "product-list/",
        productView.as_view(template_name="product.html"),
        name="products",
    ),
    path(
        "add-product/",
        productView.as_view(template_name="addProduct.html"),
        name="add-product",
    ),

]
