from django.urls import path
from .views import stock_request_view, ManageRequestsView



urlpatterns = [
    path(
        "request-list/",
        ManageRequestsView,
        name="requests",
    ),
    path(
        "create-request/",
        stock_request_view,
        name="create-request",
    ),
    path(
        "request-details/",
        stock_request_view,
        name="request-details",
    ),
]
