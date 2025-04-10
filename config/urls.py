"""
URL configuration for web_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import django
from django.contrib import admin
from django.urls import include, path, re_path
from web_project.views import SystemView
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import gettext_lazy as _
from django.conf.urls.static import static
from django.conf.urls.i18n import set_language



urlpatterns = i18n_patterns(
    path("admin/", admin.site.urls),

    path('rosetta/', include('rosetta.urls')),

    path('set_language/', set_language, name='set_language'),

    # Dashboard urls
    path("", include("apps.dashboards.urls")),

    # layouts urls
    path("", include("apps.layouts.urls")),

    # Pages urls
    path("", include("apps.pages.urls")),

    # Auth urls
    path("", include("apps.authentication.urls")),

    # Card urls
    path("", include("apps.cards.urls")),

    # UI urls
    path("", include("apps.ui.urls")),

    # Extended UI urls
    path("", include("apps.extended_ui.urls")),

    # Icons urls
    path("", include("apps.icons.urls")),

    # Forms urls
    path("", include("apps.forms.urls")),

    # FormLayouts urls
    path("", include("apps.form_layouts.urls")),

    # Tables urls
    path("", include("apps.tables.urls")),

    path("test/", include("tests.urls")),

    # Workers urls
    path("", include("apps.workers.urls")),

    # Customers Urls
    path("", include("apps.customers.urls")),

    # Products Urls
    path("", include("apps.products.urls")),

    # Orders Urls
    path("", include("apps.orders.urls")),

     # Branches Urls
    path("", include("apps.branches.urls")),

     # Sales rep Urls
    path("", include("apps.sales_rep.urls")),

     # Requests Urls
    path("", include("apps.stock_request.urls")),

     # Approved Request Urls
    path("", include("apps.approved_request.urls")),

    # Requests Urls
    path("", include("apps.stock.urls")),

    # Transfer Stock Urls
    path("", include("apps.transfer_stock.urls")),

    # Recommendation Urls
    path("", include("apps.recommendations.urls")),

    # Brand Name Urls
    path("", include("apps.brandName.urls")),

    # Generic Name Urls
    path("", include("apps.genericName.urls")),

    # Pack Size Urls
    path("", include("apps.pack_size.urls")),


    path("", include("apps.custom_clearance.urls")),


    # Old Invoice Urls
    path("", include("apps.oldinvoice.urls")),

    path('i18n/', include('django.conf.urls.i18n')),

    path('i18n/setlang/', django.views.i18n.set_language, name='set_language'),





) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = SystemView.as_view(template_name="pages_misc_error.html", status=404)
handler400 = SystemView.as_view(template_name="pages_misc_error.html", status=400)
handler500 = SystemView.as_view(template_name="pages_misc_error.html", status=500)
