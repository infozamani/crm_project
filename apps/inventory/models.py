from django.conf import settings
from django.db import models
from django.urls import reverse


class Part(models.Model):
    """قطعه یدکی."""

    name = models.CharField(max_length=255, verbose_name='نام قطعه')
    code = models.CharField(max_length=64, unique=True, verbose_name='کد قطعه')
    brand = models.CharField(max_length=128, blank=True, verbose_name='برند')
    min_stock = models.PositiveIntegerField(default=0, verbose_name='حداقل موجودی')
    max_stock = models.PositiveIntegerField(default=0, verbose_name='حداکثر موجودی')
    unit_price = models.DecimalField(max_digits=16, decimal_places=0, verbose_name='قیمت واحد (ریال)')

    class Meta:
        verbose_name = 'قطعه'
        verbose_name_plural = 'قطعات'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'

    def get_absolute_url(self):
        return reverse('inventory:part_detail', args=[self.pk])

    @property
    def current_stock(self) -> int:
        aggregate = self.transactions.aggregate(
            total_in=models.Sum('quantity', filter=models.Q(transaction_type=InventoryTransaction.TransactionType.IN)),
            total_out=models.Sum('quantity', filter=models.Q(transaction_type=InventoryTransaction.TransactionType.OUT)),
        )
        return (aggregate['total_in'] or 0) - (aggregate['total_out'] or 0)

    @property
    def is_below_minimum(self) -> bool:
        return self.current_stock < self.min_stock


class InventoryTransaction(models.Model):
    """تراکنش‌های ورود و خروج قطعات."""

    class TransactionType(models.TextChoices):
        IN = 'in', 'ورود'
        OUT = 'out', 'خروج'

    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='transactions', verbose_name='قطعه')
    transaction_type = models.CharField(max_length=8, choices=TransactionType.choices, verbose_name='نوع تراکنش')
    quantity = models.PositiveIntegerField(verbose_name='تعداد')
    date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ')
    reference_repair_order = models.ForeignKey(
        'workshop.TaskAssignment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='inventory_transactions', verbose_name='ارجاع به دستورکار تعمیر'
    )
    purchase_order_reference = models.CharField(max_length=128, blank=True, verbose_name='ارجاع به سفارش خرید')

    class Meta:
        verbose_name = 'تراکنش انبار'
        verbose_name_plural = 'تراکنش‌های انبار'
        ordering = ['-date']

    def __str__(self):
        return f'{self.get_transaction_type_display()} - {self.part} ({self.quantity})'


class PartRequest(models.Model):
    """
    درخواست قطعه توسط تکنسین از انبار (مثلاً حین انجام یک تعمیر). انباردار
    این درخواست را می‌بیند و در صورت موجود بودن، آن را «تامین» می‌کند که
    به‌صورت خودکار یک تراکنش خروج (InventoryTransaction) نیز ثبت می‌کند.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار تامین'
        FULFILLED = 'fulfilled', 'تامین‌شده'
        REJECTED = 'rejected', 'رد شده (موجود نیست)'

    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name='requests', verbose_name='قطعه')
    task_assignment = models.ForeignKey(
        'workshop.TaskAssignment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='part_requests', verbose_name='مرتبط با دستورکار تعمیر'
    )
    quantity_requested = models.PositiveIntegerField(verbose_name='تعداد درخواستی')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                       related_name='part_requests', verbose_name='درخواست‌دهنده')
    note = models.CharField(max_length=255, blank=True, verbose_name='توضیح')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, verbose_name='وضعیت')
    fulfilled_transaction = models.OneToOneField(
        InventoryTransaction, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fulfilled_request', verbose_name='تراکنش خروج مرتبط'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ درخواست')

    class Meta:
        verbose_name = 'درخواست قطعه'
        verbose_name_plural = 'درخواست‌های قطعه'
        ordering = ['-created_at']

    def __str__(self):
        return f'درخواست {self.quantity_requested} عدد «{self.part.name}»'
