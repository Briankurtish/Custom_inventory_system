from django.urls import path
from .views import customerView



urlpatterns = [
    path(
        "customers-list/",
        customerView.as_view(template_name="customers.html"),
        name="customers",
    ),
    path(
        "add-customer/",
        customerView.as_view(template_name="addCustomer.html"),
        name="add-customers",
    ),
]
