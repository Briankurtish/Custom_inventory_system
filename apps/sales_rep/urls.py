from django.urls import path
from .views import ManageSalesRepView, add_salesRep_view, update_salesRep_view, delete_salesRep_view, get_sales_rep_credit_history



urlpatterns = [
    path(
        "sales-rep-list/",
        ManageSalesRepView,
        name="sales-rep",
    ),
    path(
        "add-sales-rep/",
        add_salesRep_view,
        name="add-sales-rep",
    ),
    path("edit-sales-rep/<int:pk>/", update_salesRep_view, name="edit-sales-rep"),
    path("delete-sales-rep/<int:pk>/", delete_salesRep_view, name="delete-sales-rep"),
    path("worker/<int:worker_id>/credit-history/", get_sales_rep_credit_history, name="sales_rep_credit_history"),
]
