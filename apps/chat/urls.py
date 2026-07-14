from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.InboxView.as_view(), name='inbox'),
    path('start/', views.StartConversationView.as_view(), name='start'),
    path('<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('unread-count/', views.UnreadChatCountView.as_view(), name='unread_count'),
]
