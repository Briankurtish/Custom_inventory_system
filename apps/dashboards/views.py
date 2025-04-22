from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.workers.models import Worker, RolePrivilege
from apps.stock_request.models import StockRequest
from django.utils.translation import activate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notice
from .forms import NoticeForm


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
                    'Stock Manager': 'dashboard_stkm.html',
                    'Stock Keeper': 'dashboard_stk-keeper.html',
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


        # Add the notices to the context
        context['notices'] = Notice.objects.filter(is_active=True).order_by("-created_at")

        # Check if the user is logging in for the first time (last_login is None)
        show_password_modal = self.request.user.last_login is None
        if show_password_modal:
            # Refresh user object to ensure last_login is set
            self.request.user.refresh_from_db()

        # Add the flag to show the modal
        context['show_password_modal'] = show_password_modal



        return context


@login_required
def notice_board(request):
    notices = Notice.objects.filter(is_active=True).order_by("-created_at")
    form = NoticeForm()

    if request.method == "POST":
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user.worker_profile  # Assuming worker_profile is linked
            notice.save()
            messages.success(request, "Notice posted successfully!")
            return redirect("notice_board")

    context = TemplateLayout.init(
        request,
        {"notices": notices, "form": form}
    )

    return render(request, "new_notice.html", context)




@login_required
def delete_notice(request, pk):
    try:
        notice = Notice.objects.get(pk=pk)
        notice.delete()
        messages.success(request, "Notice deleted successfully!")
    except Notice.DoesNotExist:
        messages.error(request, "Notice not found.")
    return redirect("notice_board")
