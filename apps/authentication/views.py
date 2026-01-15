from django.views.generic import TemplateView
from django.contrib.sites.shortcuts import get_current_site
from web_project.template_helpers.theme import TemplateHelper
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.http import HttpResponseRedirect
from django.urls import reverse
from smtplib import SMTPRecipientsRefused, SMTPException
import logging

logger = logging.getLogger(__name__)


class LoginView(TemplateView):
    template_name = 'user/login.html'  # The template to render for this view

    def get(self, request, *args, **kwargs):
        """
        Display the login form on GET request.
        """
        form = AuthenticationForm()
        context = {
            'form': form,
            'layout_path': TemplateHelper.set_layout("layout_blank.html", {}),
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Handle form submission on POST request.
        """
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Authenticate the user
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Log the user in
                login(request, user)
                # Force session to be saved
                request.session.modified = True
                request.session.save()
                messages.success(request, _(f'Welcome back, {user.username}!'))
                # Get the next parameter or default to index
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                messages.error(request, _('Invalid username or password.'))
        else:
            messages.error(request, _('Please correct the errors below.'))

        context = {
            'form': form,
            'layout_path': TemplateHelper.set_layout("layout_blank.html", {}),
        }
        return self.render_to_response(context)


class LogoutView(TemplateView):
    """
    Logs the user out and redirects them to the login page or home page.
    """
    template_name = 'user/logout.html'  # Optional, if you want to show a logout page

    def get(self, request, *args, **kwargs):
        """
        Log the user out and redirect to the login page or index page.
        """
        logout(request)
        messages.info(request, _("You have been logged out successfully."))
        return redirect('auth-login-basic')  # Redirect to login page or home page (adjust the URL as necessary)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'forgot_password.html'

    def get_context_data(self, **kwargs):
        # Get the default context from the parent class
        context = super().get_context_data(**kwargs)
        # Add the layout_path context variable
        context['layout_path'] = TemplateHelper.set_layout("layout_blank.html", {})
        return context

    def form_valid(self, form):
        """
        Override form_valid to handle email sending errors gracefully.
        """
        try:
            current_site = get_current_site(self.request)
            domain = current_site.domain
            protocol = 'https' if self.request.is_secure() else 'http'

            # Try to send the password reset email
            form.save(
                request=self.request,
                use_https=self.request.is_secure(),
                domain_override=domain,
                extra_email_context={
                    'protocol': protocol,
                    'domain': domain,
                },
            )
            # If successful, redirect to the done page
            return super().form_valid(form)
        except SMTPRecipientsRefused as e:
            # Log the error for debugging
            logger.error(f"SMTP Recipients Refused error: {e}")
            # Show user-friendly error message
            messages.error(
                self.request,
                _("Unable to send password reset email. The email server rejected the request. "
                  "Please contact the administrator or try again later.")
            )
            # Return to the form with errors
            return self.form_invalid(form)
        except SMTPException as e:
            # Log the error for debugging
            logger.error(f"SMTP error: {e}")
            # Show user-friendly error message
            messages.error(
                self.request,
                _("Unable to send password reset email due to a server error. "
                  "Please contact the administrator or try again later.")
            )
            # Return to the form with errors
            return self.form_invalid(form)
        except Exception as e:
            # Log any other unexpected errors
            logger.error(f"Unexpected error sending password reset email: {e}")
            messages.error(
                self.request,
                _("An unexpected error occurred while sending the password reset email. "
                  "Please contact the administrator.")
            )
            return self.form_invalid(form)

class CustomPasswordResetViewDone(PasswordResetDoneView):
    template_name = 'forgot_password.html'

    def get_context_data(self, **kwargs):
        # Get the default context from the parent class
        context = super().get_context_data(**kwargs)
        # Add the layout_path context variable
        context['layout_path'] = TemplateHelper.set_layout("layout_blank.html", {})
        return context

    def form_valid(self, form):
        """
        Override form_valid to customize email details and use the correct domain and protocol.
        """
        current_site = get_current_site(self.request)
        domain = current_site.domain
        protocol = 'https' if self.request.is_secure() else 'http'

        # Customize email sending
        form.save(
            request=self.request,
            use_https=self.request.is_secure(),
            domain_override=domain,
            extra_email_context={
                'protocol': protocol,
                'domain': domain,
            },
        )
        return super().form_valid(form)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'forgot_password.html'

    def get_context_data(self, **kwargs):
        """
        Add the layout path and the appropriate form to the context.
        """
        # Get the default context from the parent class
        context = super().get_context_data(**kwargs)

        # Add the layout path context variable
        context['layout_path'] = TemplateHelper.set_layout("layout_blank.html", {})
        return context

    def form_valid(self, form):
        """
        Save the new password and redirect to the login page with a success message.
        """
        # Save the new password
        form.save()

        # Add a success message
        messages.success(self.request, _("Your password has been reset successfully. You can now log in with your new password."))

        # Redirect to the login page
        return HttpResponseRedirect(reverse('auth-login-basic'))

    def form_invalid(self, form):
        """
        Handle invalid form submissions (e.g., invalid token or mismatched passwords).
        """
        messages.error(self.request, _("There was an error resetting your password. Please try again."))
        return self.render_to_response(self.get_context_data(form=form))

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'forgot_password.html'

    def get_context_data(self, **kwargs):
        # Get the default context from the parent class
        context = super().get_context_data(**kwargs)
        # Add the layout_path context variable
        context['layout_path'] = TemplateHelper.set_layout("layout_blank.html", {})
        return context
