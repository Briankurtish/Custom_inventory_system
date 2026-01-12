from django.urls import path
from .views import ManageBranchView, add_branch_view, update_branch_view, delete_branch_view, BranchAuditLogView, toggle_branch_status



urlpatterns = [
    path(
        "branches-list/", ManageBranchView, name="branches",
    ),
    path(
        "branch-logs/", BranchAuditLogView, name="branch-logs",
    ),
    path(
        "add-branch/", add_branch_view, name="add-branch",
    ),
    path("edit-branch/<int:pk>/", update_branch_view, name="edit-branch"),
    path("delete-branch/<int:pk>/", delete_branch_view, name="delete-branch"),
    path("toggle-branch-status/<int:pk>/", toggle_branch_status, name="toggle-branch-status"),
]
