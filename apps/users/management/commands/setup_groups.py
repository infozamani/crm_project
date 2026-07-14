"""
دستور مدیریتی برای ایجاد گروه‌های Django متناظر با نقش‌های پروپوزال و تخصیص
مجوزهای پیش‌فرض به هر گروه. اجرا با: python manage.py setup_groups

این مجوزها هم برای کنترل واقعی دسترسی (افزودن/ویرایش/حذف) و هم برای نمایش
هوشمند منو/داشبورد بر اساس نقش استفاده می‌شوند (نگاه کنید به templates/base.html
و apps/reports/views.py که از request.user.has_perm(...) استفاده می‌کنند).
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.users.models import Role

# هر مجوز به‌صورت 'app_label.codename' مشخص می‌شود.
ROLE_PERMISSIONS = {
    Role.CEO: 'ALL',

    Role.SALES_MANAGER: [
        'customers.view_customer', 'customers.add_customer', 'customers.change_customer',
        'customers.view_salesopportunity', 'customers.add_salesopportunity', 'customers.change_salesopportunity',
        'customers.view_interaction', 'customers.add_interaction',
        'sales.view_quote', 'sales.add_quote', 'sales.change_quote',
        'sales.view_contract', 'sales.add_contract', 'sales.change_contract',
        'sales.view_check', 'sales.view_deliveryschedule',
        # بررسی و تایید/رد برآورد قیمت تکنسین‌ها
        'workshop.view_costestimate', 'workshop.change_costestimate',
        'workshop.view_servicerequest', 'workshop.add_servicerequest',
        # ارجاع دستگاه به تکنسین (مطابق گردش کار: تماس مشتری → ارجاع به تکنسین)
        'workshop.view_taskassignment', 'workshop.add_taskassignment',
        'workshop.view_technician',
    ],
    Role.SALES_REP: [
        'customers.view_customer', 'customers.add_customer',
        'customers.view_salesopportunity', 'customers.add_salesopportunity', 'customers.change_salesopportunity',
        'customers.view_interaction', 'customers.add_interaction',
        'sales.view_quote', 'sales.add_quote',
        'workshop.view_servicerequest', 'workshop.add_servicerequest',
    ],

    Role.WORKSHOP_MANAGER: [
        'workshop.view_servicerequest', 'workshop.add_servicerequest', 'workshop.change_servicerequest',
        'workshop.view_taskassignment', 'workshop.add_taskassignment', 'workshop.change_taskassignment',
        'workshop.view_repairlog',
        'workshop.view_costestimate',
        'workshop.view_technician', 'workshop.add_technician', 'workshop.change_technician',
        'workshop.view_fieldservice', 'workshop.add_fieldservice', 'workshop.change_fieldservice',
        'inventory.view_part', 'inventory.view_partrequest',
        'customers.view_customer',
    ],
    Role.TECHNICIAN: [
        # تکنسین فقط کارهای محوله به خودش، ثبت گزارش تعمیر، مأموریت‌های خودش،
        # ثبت برآورد قیمت، درخواست قطعه از انبار، و مشاهده (نه ویرایش) موجودی
        # قطعات را می‌بیند. هیچ دسترسی مالی/قرارداد/نمودار فروش ندارد.
        'workshop.view_servicerequest', 'workshop.view_taskassignment',
        'workshop.view_repairlog', 'workshop.add_repairlog',
        'workshop.view_fieldservice',
        'workshop.view_costestimate', 'workshop.add_costestimate',
        'inventory.view_part',
        'inventory.view_partrequest', 'inventory.add_partrequest',
    ],

    Role.STOREKEEPER: [
        'inventory.view_part', 'inventory.add_part', 'inventory.change_part',
        'inventory.view_inventorytransaction', 'inventory.add_inventorytransaction',
        'inventory.view_partrequest', 'inventory.change_partrequest',
        # برای اطلاع از اینکه کدام دستورکار تعمیر منتظر قطعه است
        'workshop.view_servicerequest', 'workshop.view_taskassignment',
    ],

    Role.ACCOUNTANT: [
        'customers.view_customer',
        'sales.view_quote', 'sales.view_contract', 'sales.view_check', 'sales.view_deliveryschedule',
    ],

    # حساب‌های «مشتری» هیچ مجوز مدیریتی داخلی‌ای ندارند؛ آن‌ها فقط از طریق
    # پرتال مشتری (apps.portal) و بر اساس مالکیت رکورد Customer خودشان کار
    # می‌کنند، نه از طریق سیستم Group/Permission داخلی.
    Role.CUSTOMER: [],
}


class Command(BaseCommand):
    help = 'ایجاد گروه‌های Django بر اساس نقش‌های سیستم و تخصیص مجوزهای پیش‌فرض'

    def handle(self, *args, **options):
        for role, perms in ROLE_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=role.label)

            if perms == 'ALL':
                group.permissions.set(Permission.objects.all())
            elif not perms:
                group.permissions.clear()
            else:
                pairs = [p.split('.', 1) for p in perms]
                query = Q()
                for app_label, codename in pairs:
                    query |= Q(content_type__app_label=app_label, codename=codename)
                permissions = Permission.objects.filter(query)
                group.permissions.set(permissions)

            status = 'ایجاد شد' if created else 'به‌روزرسانی شد'
            self.stdout.write(self.style.SUCCESS(f'گروه «{group.name}» {status} ({group.permissions.count()} مجوز).'))
