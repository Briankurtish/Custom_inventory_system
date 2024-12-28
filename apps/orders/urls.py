from django.urls import path
from .views import order_list, create_purchase_order, add_order_items

urlpatterns = [
    path(
        "orders-list/",  # Path for listing orders
        order_list,  # View function for listing orders
        name="orders",  # URL name for this path
    ),
    path(
        "create-order/",  # Path for creating a new order
        create_purchase_order,  # View function for creating orders
        name="create-order",  # URL name for this path
    ),
    path(
        "add-order-items/",  # Path for adding items to an order
        add_order_items,  # View function for adding items
        name="add_order_items",  # URL name for this path
    ),
]
