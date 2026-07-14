"""تابع کمکی برای ارسال اعلان به یک یا چند کاربر/گروه از هر جای پروژه."""
from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def notify_user(user, message, url=''):
    if user is None:
        return
    Notification.objects.create(recipient=user, message=message, url=url)


def notify_role(role, message, url=''):
    """ارسال اعلان به همه کاربران فعال یک نقش مشخص (مثلاً همه مدیران فروش)."""
    users = User.objects.filter(role=role, is_active=True)
    Notification.objects.bulk_create([
        Notification(recipient=u, message=message, url=url) for u in users
    ])
