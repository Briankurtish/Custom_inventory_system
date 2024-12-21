from django.urls import path
from .views import stock_request_view, ManageRequestsView, stock_request_details, approve_or_decline_request, stock_received

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
    path('stock-request/<int:request_id>/', stock_request_details, name='stock_request_details'),
    path('stock-request/<int:request_id>/action/', approve_or_decline_request, name='approve_or_decline_request'),
    path('stock-request/<int:request_id>/received/', stock_received, name='stock_received'),  # New URL pattern
]
