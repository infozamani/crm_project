from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    """نقش‌های سیستم مطابق با ماتریس دسترسی پروپوزال."""
    CEO = 'ceo', 'مدیرعامل'
    SALES_MANAGER = 'sales_manager', 'مدیر فروش'
    SALES_REP = 'sales_rep', 'کارشناس فروش'
    WORKSHOP_MANAGER = 'workshop_manager', 'مدیر تعمیرگاه'
    TECHNICIAN = 'technician', 'تکنسین'
    STOREKEEPER = 'storekeeper', 'انباردار'
    ACCOUNTANT = 'accountant', 'حسابداری'
    CUSTOMER = 'customer', 'مشتری (پرتال مشتری)'


class User(AbstractUser):
    """
    کاربر سفارشی سیستم. نقش اصلی کاربر برای دسترسی سریع در فیلد role نگه‌داری
    می‌شود، اما کنترل واقعی مجوزها از طریق Django Groups/Permissions انجام
    می‌گیرد (هر Role با یک Group هم‌نام مرتبط است).

    کاربرانی با نقش «مشتری» به هیچ‌کدام از صفحات مدیریتی داخلی دسترسی ندارند
    و فقط از طریق «پرتال مشتری» (apps.portal) با حساب خود کار می‌کنند؛ این
    محدودیت توسط CustomerPortalAccessMiddleware اعمال می‌شود.
    """
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.SALES_REP, verbose_name='نقش')
    phone_number = models.CharField(max_length=20, blank=True, verbose_name='شماره تماس')
    is_active_employee = models.BooleanField(default=True, verbose_name='کارمند فعال')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='عکس پروفایل')
    bio = models.CharField(max_length=255, blank=True, verbose_name='توضیح کوتاه (مثلاً واحد یا تخصص)')

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_ceo(self):
        return self.role == Role.CEO or self.is_superuser

    @property
    def is_sales_manager(self):
        return self.role == Role.SALES_MANAGER

    @property
    def is_sales_rep(self):
        return self.role == Role.SALES_REP

    @property
    def is_workshop_manager(self):
        return self.role == Role.WORKSHOP_MANAGER

    @property
    def is_technician(self):
        return self.role == Role.TECHNICIAN

    @property
    def is_storekeeper(self):
        return self.role == Role.STOREKEEPER

    @property
    def is_accountant(self):
        return self.role == Role.ACCOUNTANT

    @property
    def is_customer(self):
        return self.role == Role.CUSTOMER

    def get_post_login_url(self):
        """آدرس مقصد پس از ورود موفق، بر اساس نقش کاربر."""
        from django.urls import reverse
        if self.is_customer:
            return reverse('portal:dashboard')
        return reverse('reports:dashboard')

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None
