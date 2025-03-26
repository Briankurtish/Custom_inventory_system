from django.urls import path
from .views import *

urlpatterns = [
    path('clearance-dashboard/', clearance_dashboard, name='clearance_dashboard'),
    path('start-clearance-process/', add_clearance_process, name='add_clearance_process'),
    path('custom-clearance/start/', start_clearance_process, name='start_clearance_process'),
    path('custom-clearance/history/', clearance_history, name='clearance_history'),
    path('custom-logs/', view_custom_logs, name='custom_logs'),
]
