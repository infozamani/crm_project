from django.apps import AppConfig


class CustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.customers'
    verbose_name = 'مشتریان و فرصت‌های فروش'

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Customer, SalesOpportunity, Interaction
        auditlog.register(Customer)
        auditlog.register(SalesOpportunity)
        auditlog.register(Interaction)
