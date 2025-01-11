from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.workers.models import Worker
from apps.stock_request.models import StockRequest
from django.utils.translation import activate

class DashboardsView(LoginRequiredMixin, TemplateView):
    # Default fallback template
    template_name = "dashboard_analytics.html"
    
    def get_template_names(self):
        """
        Dynamically select the template based on the worker's role.
        """
        if self.request.user.is_authenticated:
            try:
                # Retrieve the worker's role
                worker = self.request.user.worker_profile
                role_template_map = {
                    'Director': 'dashboard_analytics.html',
                    'Pharmacist': 'dashboard_pharmacist.html',
                    'Marketing Director': 'dashboard_md.html',
                    'Central Stock Manager': 'dashboard_cstm.html',
                    'Stock Manager': 'dashboard_cstm.html',
                    'Stock Keeper': 'dashboard_stock_keeper.html',
                    'Accountant': 'dashboard_acc.html',
                    'Cashier': 'dashboard_cash.html',
                    'Secretary': 'dashboard_sec.html',
                    'Sales Rep': 'dashboard_cstm.html',
                    'Driver': 'dashboard_driver.html',
                    'Other': 'dashboard_analytics.html',
                }
                # Return the specific template for the role or the default
                return [role_template_map.get(worker.role, self.template_name)]
            except Worker.DoesNotExist:
                # If no worker profile exists, fallback to default template
                return [self.template_name]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        """
        Add additional context data if needed.
        """
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['role'] = getattr(self.request.user.worker_profile, 'role', 'Unknown')
        
         # Add the count of pending stock requests
        context['pending_request_count'] = StockRequest.objects.filter(status='Pending').count()
        context['accepted_request_count'] = StockRequest.objects.filter(status='Accepted').count()
        return context
