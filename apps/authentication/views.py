from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


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
        if request.method == "POST":
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                # Authenticate the user
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    # Log the user in
                    login(request, user)
                    messages.success(request, _(f'Welcome back, {user.username}!'))
                    return redirect('index')  # Redirect to homepage after login
                else:
                    messages.error(request, _('Invalid username or password.'))
            else:
                messages.error(request, _('Please correct the errors below.'))

        else:
            form = AuthenticationForm()

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
