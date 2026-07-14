from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from .models import Customer, SalesOpportunity, Interaction

User = get_user_model()


@admin.action(description='ایجاد حساب پرتال مشتری برای موارد انتخاب‌شده')
def create_portal_accounts(modeladmin, request, queryset):
    from apps.users.models import Role
    created_count = 0
    for customer in queryset:
        if customer.portal_user_id:
            continue
        base_username = f'customer{customer.pk}'
        password = get_random_string(10)
        user = User.objects.create_user(
            username=base_username, password=password,
            first_name=customer.name[:30], role=Role.CUSTOMER, is_staff=False,
        )
        customer.portal_user = user
        customer.save(update_fields=['portal_user'])
        created_count += 1
        messages.info(
            request,
            f'حساب پرتال برای «{customer.name}» ساخته شد → نام کاربری: {base_username} / رمز عبور: {password} '
            f'(این رمز را به مشتری اطلاع دهید، این پیام دیگر تکرار نمی‌شود.)'
        )
    if created_count == 0:
        messages.warning(request, 'همه موارد انتخاب‌شده از قبل حساب پرتال داشتند.')


class InteractionInline(admin.TabularInline):
    model = Interaction
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_type', 'national_or_economic_id', 'phone_number',
                     'is_verified', 'assigned_sales_rep', 'portal_user', 'created_at')
    list_filter = ('customer_type', 'is_verified', 'assigned_sales_rep')
    search_fields = ('name', 'national_or_economic_id', 'phone_number')
    date_hierarchy = 'created_at'
    actions = [create_portal_accounts]


@admin.register(SalesOpportunity)
class SalesOpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'machine_model', 'estimated_budget', 'status', 'owner', 'created_at')
    list_filter = ('status', 'owner')
    search_fields = ('title', 'customer__name', 'machine_model')
    inlines = [InteractionInline]


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('opportunity', 'interaction_type', 'date', 'created_by')
    list_filter = ('interaction_type',)
