from django.urls import path
from .views import *



urlpatterns = [
    path('search-products/', add_stock_view, name='search_products'),
    path(
        "stock/",
        ManageStockView,
        name="stock",
    ),
    path(
        "stock-logs/", StockAuditLogView, name="stock-logs",
    ),
    path(
        "branch-stock/",
        ManageBranchStockView,
        name="branch-stock",
    ),
    path(
        "stock-branch/",
        ManageStockBranchView,
        name="stock-branch",
    ),
    path(
        "add-stock/",
        add_stock_view,
        name="add-stock",
    ),
    path("update-stock/", update_stock_view, name="update_stock"),
    path(
        "update-stock/",
        update_existing_stock_view,
        name="update-stock",
    ),
    path('update-stock-entry/<int:stock_id>/', update_stock_entry_view, name='update-stock-entry'),

    path('get-branches/', get_branches, name='get-branches'),

    path('get-stock-data/', get_stock_data, name='get-stock-data'),

    path("track-stocks/", track_stocks, name="track-stocks"),

    path('delete-stock/', delete_stock_api, name='delete-stock-api'),
    path("delete-stock/<int:stock_id>/", delete_stock_page, name="delete-stock"),

    path('beginning-inventory/', add_beginning_inventory_view, name="add-beginning-inventory"),

    path('reports/inventory-register/', inventory_register, name='inventory_register'),
]
