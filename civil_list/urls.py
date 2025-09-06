from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # include the hr app WITH an explicit namespace
    path('hr/', include(('hr.urls', 'hr'), namespace='hr')),
    
    # ✅ add this line
    path('i18n/', include('django.conf.urls.i18n')),

    # optional: send / to /hr/portal/
    path('', RedirectView.as_view(url='/hr/portal/', permanent=False)),

    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
