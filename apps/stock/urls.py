from django.urls import path
from .views import stockView



urlpatterns = [
    path(
        "stock/",
        stockView.as_view(template_name="stock.html"),
        name="stock",
    ),
    path(
        "update-stock/",
        stockView.as_view(template_name="updateStock.html"),
        name="update-stock",
    ),
]
