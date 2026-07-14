from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.CustomerListView.as_view(), name='customer_list'),
    path('new/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    path('<int:pk>/create-portal-account/', views.CreatePortalAccountView.as_view(), name='customer_create_portal_account'),

    path('opportunities/', views.OpportunityListView.as_view(), name='opportunity_list'),
    path('opportunities/new/', views.OpportunityCreateView.as_view(), name='opportunity_create'),
    path('opportunities/<int:pk>/', views.OpportunityDetailView.as_view(), name='opportunity_detail'),
    path('opportunities/<int:pk>/edit/', views.OpportunityUpdateView.as_view(), name='opportunity_update'),
    path('opportunities/<int:opportunity_pk>/interactions/new/',
         views.InteractionCreateView.as_view(), name='interaction_create'),
]
