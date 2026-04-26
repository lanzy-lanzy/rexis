"""
URL configuration for rexis project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from portal.views import home
from users.views import login_view, logout_view
from core.views import comprehensive_reports, comprehensive_reports_pdf, global_search

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', include('portal.urls')),
    path('proposals/', include('proposals.urls')),
    path('research/', include('research.urls')),
    path('extension/', include('extension.urls')),
    path('users/', include('users.urls')),
    path('search/', global_search, name='global_search'),
    path('reports/', comprehensive_reports, name='comprehensive_reports'),
    path('reports/pdf/', comprehensive_reports_pdf, name='comprehensive_reports_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
