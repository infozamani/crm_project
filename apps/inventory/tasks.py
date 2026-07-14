from celery import shared_task
from django.core.mail import mail_admins


@shared_task
def notify_low_stock(part_id):
    """ارسال هشدار کمبود موجودی به مدیران سیستم (Celery task آسنکرون)."""
    from .models import Part
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return
    mail_admins(
        subject=f'هشدار کمبود موجودی: {part.name}',
        message=(
            f'موجودی فعلی قطعه {part.name} ({part.code}) به {part.current_stock} رسیده است '
            f'که کمتر از حداقل تعیین‌شده ({part.min_stock}) می‌باشد.'
        ),
    )
