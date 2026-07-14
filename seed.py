#!/usr/bin/env python
"""
اسکریپت پر کردن دیتابیس با داده‌های نمونه برای تست.
اجرا: python seed.py
"""
import os
import random
from datetime import timedelta
from decimal import Decimal

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local')
django.setup()

from django.core.management import call_command  # noqa: E402
from django.utils import timezone  # noqa: E402

from apps.customers.models import Customer, SalesOpportunity, Interaction  # noqa: E402
from apps.sales.models import Quote, QuoteItem, Contract, Check, DeliverySchedule  # noqa: E402
from apps.users.models import User, Role  # noqa: E402


def create_users():
    from django.contrib.auth.models import Group

    users = {}
    sample_users = [
        ('ceo1', Role.CEO, 'مدیر', 'عامل'),
        ('salesmgr1', Role.SALES_MANAGER, 'مدیر', 'فروش'),
        ('salesrep1', Role.SALES_REP, 'کارشناس', 'فروش'),
        ('workshopmgr1', Role.WORKSHOP_MANAGER, 'مدیر', 'تعمیرگاه'),
        ('tech1', Role.TECHNICIAN, 'تکنسین', 'اول'),
        ('store1', Role.STOREKEEPER, 'انباردار', 'اول'),
        ('accountant1', Role.ACCOUNTANT, 'حسابدار', 'اول'),
    ]
    for username, role, first, last in sample_users:
        user, created = User.objects.get_or_create(
            username=username,
            defaults=dict(role=role, first_name=first, last_name=last, email=f'{username}@example.com')
        )
        if created:
            user.set_password('Passw0rd!')
            user.is_staff = True
            user.save()
        # عضویت کاربر در گروه Django متناظر با نقش او؛ بدون این مرحله،
        # has_perm() همیشه False برمی‌گرداند و منو/دسترسی‌ها کار نمی‌کنند.
        group, _ = Group.objects.get_or_create(name=role.label)
        user.groups.add(group)
        users[username] = user
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'AdminPass123!')
        print('کاربر ادمین ساخته شد: admin / AdminPass123!')
    return users


def create_customers(users):
    customers = []
    names = ['شرکت راهسازی البرز', 'پیمانکاری جاده ابریشم', 'گروه صنعتی زاگرس',
              'شرکت عمران پارس', 'مقاطعه‌کاری کوهسار']
    for i, name in enumerate(names):
        customer, _ = Customer.objects.get_or_create(
            national_or_economic_id=f'10{i:09d}'[:11],
            defaults=dict(
                name=name,
                customer_type=Customer.CustomerType.LEGAL,
                phone_number=f'0912000{i:04d}',
                address=f'تهران، خیابان نمونه {i+1}',
                is_verified=True,
                assigned_sales_rep=users['salesrep1'],
            )
        )
        customers.append(customer)
    return customers


def create_opportunities(customers, users):
    opportunities = []
    machines = ['بیل مکانیکی CAT 320', 'لودر ولوو L60', 'غلتک هامم HD12', 'بولدوزر کوماتسو D65']
    statuses = list(SalesOpportunity.Status)
    for i, customer in enumerate(customers):
        opp, _ = SalesOpportunity.objects.get_or_create(
            customer=customer,
            title=f'پروژه تأمین ماشین‌آلات {i+1}',
            defaults=dict(
                machine_model=random.choice(machines),
                estimated_budget=random.randint(500, 5000) * 1_000_000,
                status=random.choice(statuses),
                owner=users['salesrep1'],
            )
        )
        opportunities.append(opp)
        Interaction.objects.get_or_create(
            opportunity=opp,
            interaction_type=Interaction.InteractionType.CALL,
            date=timezone.now() - timedelta(days=i),
            defaults=dict(notes='تماس اولیه جهت بررسی نیاز مشتری.', created_by=users['salesrep1']),
        )
    return opportunities


def create_quotes_and_contracts(opportunities, customers, users):
    for i, opp in enumerate(opportunities[:3]):
        quote, created = Quote.objects.get_or_create(
            opportunity=opp,
            valid_until=timezone.now().date() + timedelta(days=30),
            defaults=dict(discount_percent=5, tax_percent=9, created_by=users['salesrep1']),
        )
        if created:
            QuoteItem.objects.create(quote=quote, description=opp.machine_model, quantity=1,
                                      unit_price=opp.estimated_budget)
            QuoteItem.objects.create(quote=quote, description='هزینه حمل و نصب', quantity=1,
                                      unit_price=50_000_000)

        contract, created = Contract.objects.get_or_create(
            customer=opp.customer,
            quote=quote,
            defaults=dict(
                contract_type=Contract.ContractType.INSTALLMENT,
                signed_date=timezone.now().date(),
                total_amount=quote.total_amount,
                down_payment=quote.total_amount * Decimal('0.3'),
                installments_count=6,
                installment_amount=(quote.total_amount * Decimal('0.7')) / 6,
                status=Contract.Status.ACTIVE,
                created_by=users['salesmgr1'],
            )
        )
        if created:
            for j in range(1, 4):
                Check.objects.create(
                    contract=contract,
                    check_number=f'CHK-{contract.id}-{j}',
                    due_date=timezone.now().date() + timedelta(days=30 * j),
                    amount=contract.installment_amount,
                    issuing_bank='بانک ملت',
                )
            DeliverySchedule.objects.create(
                contract=contract,
                scheduled_date=timezone.now().date() + timedelta(days=15),
                description='تحویل دستگاه به کارگاه پروژه',
            )


def create_workshop_samples(customers, users):
    from apps.workshop.models import Technician, ServiceRequest, TaskAssignment, RepairLog, FieldService

    tech_user = users['tech1']
    technician, _ = Technician.objects.get_or_create(
        user=tech_user, defaults=dict(specialty='موتور و هیدرولیک', rank='ارشد')
    )

    for i, customer in enumerate(customers[:2]):
        sr, created = ServiceRequest.objects.get_or_create(
            customer=customer, machine_identifier=f'CH-{1000+i}',
            defaults=dict(fault_type='نشتی روغن هیدرولیک', description='بررسی و تعویض واشرها',
                          status=ServiceRequest.Status.IN_REPAIR),
        )
        if created:
            assignment = TaskAssignment.objects.create(
                service_request=sr, technician=technician, start_date=timezone.now().date()
            )
            RepairLog.objects.create(
                assignment=assignment, date=timezone.now().date(),
                parts_used='واشر هیدرولیک x2', hours_spent=3.5, notes='تعویض واشر و آزمایش فشار.'
            )
    FieldService.objects.get_or_create(
        service_request=ServiceRequest.objects.first(), technician=technician,
        defaults=dict(address='کارگاه پروژه جاده ابریشم', date=timezone.now().date() + timedelta(days=2),
                      status=FieldService.Status.SCHEDULED)
    )


def create_inventory_samples():
    from apps.inventory.models import Part, InventoryTransaction

    parts_data = [
        ('فیلتر روغن', 'FLT-001', 'CAT', 5, 100, 500000),
        ('واشر هیدرولیک', 'GSK-002', 'Volvo', 10, 200, 150000),
        ('تسمه پروانه', 'BLT-003', 'Komatsu', 3, 50, 800000),
    ]
    for name, code, brand, min_stock, max_stock, price in parts_data:
        part, created = Part.objects.get_or_create(
            code=code, defaults=dict(name=name, brand=brand, min_stock=min_stock,
                                       max_stock=max_stock, unit_price=price)
        )
        if created:
            InventoryTransaction.objects.create(
                part=part, transaction_type=InventoryTransaction.TransactionType.IN,
                quantity=min_stock * 2, purchase_order_reference=f'PO-{code}'
            )
            InventoryTransaction.objects.create(
                part=part, transaction_type=InventoryTransaction.TransactionType.OUT,
                quantity=max(min_stock - 1, 1)
            )


def main():
    print('در حال اجرای پیکربندی گروه‌های دسترسی...')
    call_command('setup_groups')
    print('در حال ساخت کاربران نمونه...')
    users = create_users()
    print('در حال ساخت مشتریان نمونه...')
    customers = create_customers(users)
    print('در حال ساخت فرصت‌های فروش نمونه...')
    opportunities = create_opportunities(customers, users)
    print('در حال ساخت پیش‌فاکتور و قرارداد نمونه...')
    create_quotes_and_contracts(opportunities, customers, users)
    print('در حال ساخت نمونه‌های تعمیرگاه...')
    create_workshop_samples(customers, users)
    print('در حال ساخت نمونه‌های انبار...')
    create_inventory_samples()
    print('داده‌های نمونه با موفقیت ایجاد شدند. ✅')


if __name__ == '__main__':
    main()
