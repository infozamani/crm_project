from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.PartListView.as_view(), name='part_list'),
    path('new/', views.PartCreateView.as_view(), name='part_create'),
    path('<int:pk>/', views.PartDetailView.as_view(), name='part_detail'),
    path('<int:pk>/edit/', views.PartUpdateView.as_view(), name='part_update'),
    path('<int:pk>/delete/', views.PartDeleteView.as_view(), name='part_delete'),

    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/new/', views.TransactionCreateView.as_view(), name='transaction_create'),

    path('reports/turnover/', views.TurnoverReportView.as_view(), name='turnover_report'),
    path('reports/turnover/export.csv', views.turnover_report_csv, name='turnover_report_csv'),

    path('part-requests/', views.PartRequestListView.as_view(), name='part_request_list'),
    path('part-requests/new/', views.PartRequestCreateView.as_view(), name='part_request_create'),
    path('part-requests/<int:pk>/fulfill/', views.fulfill_part_request, name='part_request_fulfill'),
    path('part-requests/<int:pk>/reject/', views.reject_part_request, name='part_request_reject'),
]
