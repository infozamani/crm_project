from django.contrib import admin
from .models import Quote, QuoteItem, Contract, Check, DeliverySchedule


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('number', 'opportunity', 'valid_until', 'total_amount', 'status', 'created_at')
    readonly_fields = ('number',)
    inlines = [QuoteItemInline]
    search_fields = ('number', 'opportunity__title')

    def total_amount(self, obj):
        return f'{obj.total_amount:,.0f}'
    total_amount.short_description = 'مبلغ کل'


class CheckInline(admin.TabularInline):
    model = Check
    extra = 0


class DeliveryScheduleInline(admin.TabularInline):
    model = DeliverySchedule
    extra = 0


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'contract_type', 'signed_date', 'total_amount', 'status', 'is_confirmed_by_customer')
    list_filter = ('contract_type', 'status', 'is_confirmed_by_customer')
    search_fields = ('customer__name',)
    inlines = [CheckInline, DeliveryScheduleInline]


@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ('check_number', 'contract', 'due_date', 'amount', 'issuing_bank', 'status')
    list_filter = ('status',)
    date_hierarchy = 'due_date'


@admin.register(DeliverySchedule)
class DeliveryScheduleAdmin(admin.ModelAdmin):
    list_display = ('description', 'contract', 'scheduled_date', 'is_completed')
    list_filter = ('is_completed',)
