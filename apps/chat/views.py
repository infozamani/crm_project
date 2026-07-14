from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView

from .models import Conversation, Message

User = get_user_model()


class InboxView(LoginRequiredMixin, ListView):
    """لیست گفتگوهای کاربر جاری، مرتب‌شده بر اساس آخرین پیام."""
    model = Conversation
    template_name = 'chat/inbox.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related('participants', 'messages')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        conversations = Conversation.objects.filter(participants=user).prefetch_related('participants', 'messages')
        ctx['conversation_rows'] = [
            {
                'conversation': c,
                'other': c.other_participant(user),
                'last_message': c.last_message(),
                'unread_count': c.unread_count_for(user),
            }
            for c in conversations
        ]
        # فقط کاربران داخلی (غیر مشتری) برای شروع گفتگوی جدید قابل انتخاب هستند
        ctx['staff_users'] = User.objects.filter(is_active=True).exclude(pk=user.pk).exclude(role='customer')
        return ctx


class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = 'chat/conversation_detail.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['other'] = self.object.other_participant(self.request.user)
        return ctx

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.object.messages.exclude(sender=request.user).update(is_read=True)
        return response

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(conversation=self.object, sender=request.user, content=content)
        return redirect('chat:conversation_detail', pk=self.object.pk)


class StartConversationView(LoginRequiredMixin, View):
    """شروع یا بازکردن یک گفتگوی دو نفره با کاربر دیگر."""

    def post(self, request):
        other_id = request.POST.get('user')
        other = get_object_or_404(User, pk=other_id)
        conversation = Conversation.objects.filter(participants=request.user).filter(participants=other).first()
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.set([request.user, other])
        return redirect('chat:conversation_detail', pk=conversation.pk)


class UnreadChatCountView(LoginRequiredMixin, View):
    def get(self, request):
        count = sum(
            c.unread_count_for(request.user)
            for c in Conversation.objects.filter(participants=request.user)
        )
        return JsonResponse({'unread_count': count})
