from django.urls import path
from .views import approvedRequestView



urlpatterns = [
    path(
        "approved-request-list/",
        approvedRequestView.as_view(template_name="approved-requests.html"),
        name="approved-requests",
    ),
    path(
        "approved-details/",
        approvedRequestView.as_view(template_name="approvedDetails.html"),
        name="approved-details",
    ),
]
