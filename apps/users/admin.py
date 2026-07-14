from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'phone_number', 'is_active_employee', 'is_staff')
    list_filter = ('role', 'is_active_employee', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('اطلاعات تکمیلی', {'fields': ('role', 'phone_number', 'is_active_employee')}),
    )
