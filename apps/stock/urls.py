from django.urls import path
from .views import add_stock_view, ManageStockView, update_stock_entry_view, update_existing_stock_view, get_branches, get_stock_data, ManageStockBranchView, track_stocks



urlpatterns = [
    path('search-products/', add_stock_view, name='search_products'),
    path(
        "stock/",
        ManageStockView,
        name="stock",
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
    path(
        "update-stock/",
        update_existing_stock_view,
        name="update-stock",
    ),
    path('update-stock-entry/<int:stock_id>/', update_stock_entry_view, name='update-stock-entry'),
    
    path('get-branches/', get_branches, name='get-branches'),
    
    path('get-stock-data/', get_stock_data, name='get-stock-data'),
    
    path("track-stocks/", track_stocks, name="track-stocks"),
]
