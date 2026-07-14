from django.contrib import admin
from .models import (Technician, ServiceRequest, ServiceRequestImage, ServiceRequestMedia,
                       TaskAssignment, RepairLog, FieldService, CostEstimate)


class ServiceRequestImageInline(admin.TabularInline):
    model = ServiceRequestImage
    extra = 0


class ServiceRequestMediaInline(admin.TabularInline):
    model = ServiceRequestMedia
    extra = 0
    readonly_fields = ('media_type', 'uploaded_at')


class TaskAssignmentInline(admin.TabularInline):
    model = TaskAssignment
    extra = 0


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'rank')


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('machine_identifier', 'customer', 'fault_type', 'status', 'received_at', 'customer_rating')
    list_filter = ('status', 'customer_rating')
    search_fields = ('machine_identifier', 'customer__name')
    inlines = [ServiceRequestImageInline, ServiceRequestMediaInline, TaskAssignmentInline]


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'technician', 'start_date', 'end_date')


@admin.register(RepairLog)
class RepairLogAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'date', 'hours_spent')


@admin.register(FieldService)
class FieldServiceAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'technician', 'date', 'status')
    list_filter = ('status',)


@admin.register(CostEstimate)
class CostEstimateAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'estimated_cost', 'status', 'created_by', 'reviewed_by', 'created_at')
    list_filter = ('status',)
