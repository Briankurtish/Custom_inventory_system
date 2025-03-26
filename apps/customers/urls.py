from django.urls import path
from .views import ManageCustomerView, customer_view, delete_customer_view, get_credit_report, CustomerAuditLogView



urlpatterns = [
    path(
        "customers-list/", ManageCustomerView, name="customers",
    ),
    path(
        "customer-logs/", CustomerAuditLogView, name="customer-logs",
    ),
    path(
        "add-customer/", customer_view, name="add-customers",
    ),

    path("edit-customer/<int:pk>/", customer_view, name="edit-customer"),
    path("delete-customer/<int:pk>/", delete_customer_view, name="delete-customer"),

    path('credit-report/<int:customer_id>/', get_credit_report, name='credit_report'),
]
