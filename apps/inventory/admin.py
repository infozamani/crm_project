from django.contrib import admin
from .models import Part, InventoryTransaction, PartRequest


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'brand', 'min_stock', 'max_stock', 'unit_price', 'current_stock_display')
    search_fields = ('name', 'code', 'brand')

    def current_stock_display(self, obj):
        return obj.current_stock
    current_stock_display.short_description = 'موجودی فعلی'


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('part', 'transaction_type', 'quantity', 'date', 'purchase_order_reference')
    list_filter = ('transaction_type',)
    date_hierarchy = 'date'


@admin.register(PartRequest)
class PartRequestAdmin(admin.ModelAdmin):
    list_display = ('part', 'quantity_requested', 'requested_by', 'status', 'created_at')
    list_filter = ('status',)
