from django.urls import path
from .views import add_stock_view, ManageStockView, update_stock_entry_view, update_existing_stock_view



urlpatterns = [
    path('search-products/', add_stock_view, name='search_products'),
    path(
        "stock/",
        ManageStockView,
        name="stock",
    ),
    path(
        "add-stock/",
        add_stock_view,
        name="add-stock",
    ),
    path(
        "update-stock/",
        update_existing_stock_view,
        name="update-stock",
    ),
    path('update-stock-entry/<int:stock_id>/', update_stock_entry_view, name='update-stock-entry'),
]
