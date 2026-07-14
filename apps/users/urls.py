from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.CRMLoginView.as_view(), name='login'),
    path('logout/', views.CRMLogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('password/', views.CRMPasswordChangeView.as_view(), name='password_change'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
]
