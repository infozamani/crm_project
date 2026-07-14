from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventory'
    verbose_name = 'انبار و قطعات یدکی'

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Part, InventoryTransaction, PartRequest
        auditlog.register(Part)
        auditlog.register(InventoryTransaction)
        auditlog.register(PartRequest)
        import apps.inventory.signals  # noqa
