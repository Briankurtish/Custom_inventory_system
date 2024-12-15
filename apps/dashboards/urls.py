from django.urls import path
from .views import DashboardsView



urlpatterns = [
    path(
        "dashboard/",
        DashboardsView.as_view(template_name="dashboard_analytics.html"),
        name="index",
    ),
    path(
        "dashboard-phar",
        DashboardsView.as_view(template_name="dashboard_pharmacist.html"),
        name="index-phar",
    ),
    path(
        "dashboard-cstm",
        DashboardsView.as_view(template_name="dashboard_cstm.html"),
        name="index-cstm",
    ),
    path(
        "dashboard-sec",
        DashboardsView.as_view(template_name="dashboard_sec.html"),
        name="index-sec",
    ),
]
