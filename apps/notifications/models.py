from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    اعلان داخلی سیستم برای یک کاربر مشخص (مثلاً «کار جدید به شما محول شد» یا
    «موجودی قطعه X کم شد»). این اعلان‌ها در زنگوله بالای صفحه نمایش داده
    می‌شوند و مکمل ایمیل‌های Celery برای رویدادهای حیاتی (مثل کمبود موجودی) هستند.
    """
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='notifications', verbose_name='گیرنده')
    message = models.CharField(max_length=255, verbose_name='پیام')
    url = models.CharField(max_length=255, blank=True, verbose_name='لینک مرتبط')
    is_read = models.BooleanField(default=False, verbose_name='خوانده‌شده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ')

    class Meta:
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.message
