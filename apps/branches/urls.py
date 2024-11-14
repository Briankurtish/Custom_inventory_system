from django.urls import path
from .views import branchView



urlpatterns = [
    path(
        "branches-list/",
        branchView.as_view(template_name="branches.html"),
        name="branches",
    ),
    path(
        "add-branch/",
        branchView.as_view(template_name="addBranch.html"),
        name="add-branch",
    ),
]
