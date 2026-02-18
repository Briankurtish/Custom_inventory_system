from django.urls import path
from . import views

urlpatterns = [
    # Main dashboard
    path('', views.reports_dashboard, name='reports_dashboard'),

    # Client financial reports
    path('client-financial/', views.client_financial_report, name='client_financial_report'),
    path('client/<int:customer_id>/', views.client_detail_report, name='client_detail_report'),

    # Regional performance
    path('regional-performance/', views.regional_performance_report, name='regional_performance_report'),

    # Sales agent performance
    path('sales-agent-performance/', views.sales_agent_performance_report, name='sales_agent_performance_report'),

    # Financial summary
    path('financial-summary/', views.financial_summary_report, name='financial_summary_report'),

    # Debt analysis
    path('debt-analysis/', views.debt_analysis_report, name='debt_analysis_report'),

    # Inventory & Product Reports
    path('inventory-levels/', views.inventory_levels_report, name='inventory_levels_report'),
    path('product-performance/', views.product_performance_report, name='product_performance_report'),
    path('stock-movement/', views.stock_movement_report, name='stock_movement_report'),
    path('inventory-valuation/', views.inventory_valuation_report, name='inventory_valuation_report'),

    # Export
    path('export/<str:report_type>/', views.export_report, name='export_report'),
]
