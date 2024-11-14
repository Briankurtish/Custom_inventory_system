from django.urls import path
from .views import requestView



urlpatterns = [
    path(
        "request-list/",
        requestView.as_view(template_name="requests.html"),
        name="requests",
    ),
    path(
        "create-request/",
        requestView.as_view(template_name="createRequests.html"),
        name="create-request",
    ),
]
