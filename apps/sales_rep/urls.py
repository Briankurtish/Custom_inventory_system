from django.urls import path
from .views import salesRepView



urlpatterns = [
    path(
        "sales-rep-list/",
        salesRepView.as_view(template_name="sales-rep.html"),
        name="sales-rep",
    ),
    path(
        "add-sales-rep/",
        salesRepView.as_view(template_name="addSalesRep.html"),
        name="add-sales-rep",
    ),
]
