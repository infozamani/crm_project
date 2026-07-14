from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """
    یک گفتگوی دو نفره بین دو کاربر داخلی سازمان (مثلاً مدیر فروش و تکنسین).
    این نسخه اول یک پیام‌رسان ساده (نه real-time) برای هماهنگی داخلی تیم‌هاست؛
    نسخه realtime واقعی (با WebSocket) می‌تواند در آینده جایگزین آن شود.
    """
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'گفتگو'
        verbose_name_plural = 'گفتگوها'

    def __str__(self):
        return ' / '.join(str(p) for p in self.participants.all())

    def other_participant(self, user):
        return self.participants.exclude(pk=user.pk).first()

    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count_for(self, user):
        return self.messages.exclude(sender=user).filter(is_read=False).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(verbose_name='متن پیام')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'پیام'
        verbose_name_plural = 'پیام‌ها'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender}: {self.content[:30]}'
