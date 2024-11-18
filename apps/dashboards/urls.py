from django.urls import path
from .views import DashboardsView



urlpatterns = [
    path(
        "",
        DashboardsView.as_view(template_name="dashboard_analytics.html"),
        name="index",
    ),
    path(
        "dashboard-wm",
        DashboardsView.as_view(template_name="dashboard_wm.html"),
        name="index-wm",
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
