from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('quotes/', views.QuoteListView.as_view(), name='quote_list'),
    path('quotes/new/', views.quote_create_or_update, name='quote_create'),
    path('quotes/<int:pk>/', views.QuoteDetailView.as_view(), name='quote_detail'),
    path('quotes/<int:pk>/edit/', views.quote_create_or_update, name='quote_update'),
    path('quotes/<int:pk>/delete/', views.QuoteDeleteView.as_view(), name='quote_delete'),
    path('quotes/<int:pk>/send/', views.SendQuoteToCustomerView.as_view(), name='quote_send'),

    path('contracts/', views.ContractListView.as_view(), name='contract_list'),
    path('contracts/new/', views.contract_create_or_update, name='contract_create'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract_detail'),
    path('contracts/<int:pk>/edit/', views.contract_create_or_update, name='contract_update'),
    path('contracts/<int:pk>/delete/', views.ContractDeleteView.as_view(), name='contract_delete'),
]
