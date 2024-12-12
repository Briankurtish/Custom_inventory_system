from django.urls import path
from .views import ManageCustomerView, customer_view, delete_customer_view



urlpatterns = [
    path(
        "customers-list/", ManageCustomerView, name="customers",
    ),
    path(
        "add-customer/", customer_view, name="add-customers",
    ),
    
    path("edit-customer/<int:pk>/", customer_view, name="edit-customer"),
    path("delete-customer/<int:pk>/", delete_customer_view, name="delete-customer"),
]
