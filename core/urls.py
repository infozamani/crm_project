"""تنظیمات اصلی URL پروژه."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.reports.urls', namespace='reports')),
    path('accounts/', include('apps.users.urls', namespace='users')),
    path('customers/', include('apps.customers.urls', namespace='customers')),
    path('sales/', include('apps.sales.urls', namespace='sales')),
    path('workshop/', include('apps.workshop.urls', namespace='workshop')),
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    path('portal/', include('apps.portal.urls', namespace='portal')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('chat/', include('apps.chat.urls', namespace='chat')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
