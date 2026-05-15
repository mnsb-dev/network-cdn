from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from devices import views as devices_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', devices_views.dashboard, name='dashboard'),
    path('automation/', include('automation.urls')),
    path('', devices_views.dashboard, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)