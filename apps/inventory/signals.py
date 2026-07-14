"""
سیگنال هشدار کمبود موجودی: هر بار که تراکنش خروج ثبت می‌شود، بررسی می‌شود که
آیا موجودی قطعه به کمتر از حداقل رسیده است؛ در این صورت یک تسک Celery برای
اطلاع‌رسانی به انباردار/مدیر فروش ارسال می‌شود.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import InventoryTransaction

logger = logging.getLogger(__name__)


@receiver(post_save, sender=InventoryTransaction)
def check_low_stock(sender, instance, created, **kwargs):
    if not created:
        return
    part = instance.part
    if part.is_below_minimum:
        from .tasks import notify_low_stock
        notify_low_stock.delay(part.id)
        logger.info('موجودی قطعه %s کمتر از حداقل شد.', part.code)
