from django.urls import path
from .views import TransferedStockView



urlpatterns = [
    path(
        "transfer-stock-list/",
        TransferedStockView.as_view(template_name="transfer_stock.html"),
        name="transfer-stock",
    ),
    path(
        "transfer-details/",
        TransferedStockView.as_view(template_name="transfer_details.html"),
        name="transfer-details",
    ),
]
