from django.apps import AppConfig


class SalesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sales'
    verbose_name = 'پیش‌فاکتور و قراردادها'

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Quote, Contract, Check, DeliverySchedule
        auditlog.register(Quote)
        auditlog.register(Contract)
        auditlog.register(Check)
        auditlog.register(DeliverySchedule)
