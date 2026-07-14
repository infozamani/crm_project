from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.PortalDashboardView.as_view(), name='dashboard'),

    path('service-requests/', views.PortalServiceRequestListView.as_view(), name='service_request_list'),
    path('service-requests/new/', views.PortalServiceRequestCreateView.as_view(), name='service_request_create'),
    path('service-requests/<int:pk>/', views.PortalServiceRequestDetailView.as_view(), name='service_request_detail'),
    path('service-requests/<int:pk>/rate/', views.PortalRateServiceRequestView.as_view(), name='service_request_rate'),

    path('quotes/', views.PortalQuoteListView.as_view(), name='quote_list'),
    path('quotes/<int:pk>/', views.PortalQuoteDetailView.as_view(), name='quote_detail'),
    path('quotes/<int:pk>/respond/', views.PortalQuoteRespondView.as_view(), name='quote_respond'),

    path('contracts/', views.PortalContractListView.as_view(), name='contract_list'),
    path('contracts/<int:pk>/', views.PortalContractDetailView.as_view(), name='contract_detail'),
    path('contracts/<int:pk>/confirm/', views.PortalContractConfirmView.as_view(), name='contract_confirm'),
]
