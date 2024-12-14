from django.urls import path
from .views import update_stock_view



urlpatterns = [
    path('search-products/', update_stock_view, name='search_products'),
    path(
        "stock/",
        update_stock_view,
        name="stock",
    ),
    path(
        "update-stock/",
        update_stock_view,
        name="update-stock",
    ),
]
