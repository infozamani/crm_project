from django.urls import path
from . import views

app_name = 'workshop'

urlpatterns = [
    path('', views.ServiceRequestListView.as_view(), name='service_request_list'),
    path('new/', views.service_request_create_or_update, name='service_request_create'),
    path('<int:pk>/', views.ServiceRequestDetailView.as_view(), name='service_request_detail'),
    path('<int:pk>/edit/', views.service_request_create_or_update, name='service_request_update'),
    path('<int:pk>/delete/', views.ServiceRequestDeleteView.as_view(), name='service_request_delete'),
    path('<int:service_request_pk>/assign/', views.TaskAssignmentCreateView.as_view(), name='assignment_create'),
    path('assignments/<int:assignment_pk>/repair-log/new/',
         views.RepairLogCreateView.as_view(), name='repair_log_create'),

    path('technicians/', views.TechnicianListView.as_view(), name='technician_list'),
    path('technicians/new/', views.TechnicianCreateView.as_view(), name='technician_create'),

    path('field-services/', views.FieldServiceListView.as_view(), name='field_service_list'),
    path('field-services/new/', views.FieldServiceCreateView.as_view(), name='field_service_create'),
    path('field-services/<int:pk>/edit/', views.FieldServiceUpdateView.as_view(), name='field_service_update'),

    path('<int:service_request_pk>/estimates/new/', views.CostEstimateCreateView.as_view(), name='cost_estimate_create'),
    path('estimates/pending/', views.CostEstimateListView.as_view(), name='cost_estimate_pending_list'),
    path('estimates/<int:pk>/', views.CostEstimateDetailView.as_view(), name='cost_estimate_detail'),
    path('estimates/<int:pk>/approve/', views.approve_cost_estimate, name='cost_estimate_approve'),
    path('estimates/<int:pk>/reject/', views.reject_cost_estimate, name='cost_estimate_reject'),
]
