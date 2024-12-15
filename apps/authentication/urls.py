from django.urls import path
from .views import LoginView, LogoutView


urlpatterns = [
    path(
        "",
        LoginView.as_view(template_name="auth_login_basic.html"),
        name="auth-login-basic",
    ),
    path(
        "auth/logout/",
        LogoutView.as_view(template_name="logout.html"),
        name="logout",
    ),
    # path(
    #     "auth/register/",
    #     LoginView.as_view(template_name="auth_register_basic.html"),
    #     name="auth-register-basic",
    # ),
    # path(
    #     "auth/forgot_password/",
    #     LoginView.as_view(template_name="auth_forgot_password_basic.html"),
    #     name="auth-forgot-password-basic",
    # ),
]
