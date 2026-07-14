from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('<int:pk>/go/', views.NotificationReadRedirectView.as_view(), name='read_redirect'),
    path('mark-all-read/', views.MarkAllReadView.as_view(), name='mark_all_read'),
    path('unread-count/', views.NotificationBellPartialView.as_view(), name='unread_count'),
]
