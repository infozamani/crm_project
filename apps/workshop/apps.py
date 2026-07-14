from django.apps import AppConfig


class WorkshopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workshop'
    verbose_name = 'تعمیرگاه و خدمات پس از فروش'

    def ready(self):
        from auditlog.registry import auditlog
        from .models import ServiceRequest, TaskAssignment, RepairLog, FieldService, CostEstimate
        auditlog.register(ServiceRequest)
        auditlog.register(TaskAssignment)
        auditlog.register(RepairLog)
        auditlog.register(FieldService)
        auditlog.register(CostEstimate)
