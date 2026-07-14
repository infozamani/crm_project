from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationReadRedirectView(LoginRequiredMixin, View):
    """کلیک روی یک اعلان: علامت‌گذاری به‌عنوان خوانده‌شده و انتقال به لینک مرتبط."""

    def get(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
        if not notif.is_read:
            notif.is_read = True
            notif.save(update_fields=['is_read'])
        return redirect(notif.url or 'reports:dashboard')


class MarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return redirect(request.META.get('HTTP_REFERER', 'reports:dashboard'))


class NotificationBellPartialView(LoginRequiredMixin, View):
    """برای فراخوانی دوره‌ای با جاوااسکریپت (بروزرسانی تعداد اعلان‌های نخوانده)."""

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'unread_count': count})
