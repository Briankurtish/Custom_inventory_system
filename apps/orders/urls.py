from django.urls import path
from .views import orderView



urlpatterns = [
    path(
        "orders-list/",
        orderView.as_view(template_name="orderList.html"),
        name="orders",
    ),
    path(
        "create-order/",
        orderView.as_view(template_name="createOrder.html"),
        name="create-order",
    ),
    path(
        "order-detail/",
        orderView.as_view(template_name="orderDetails.html"),
        name="order-detail",
    ),
]
