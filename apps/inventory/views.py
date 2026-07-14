import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, View

from apps.notifications.utils import notify_role, notify_user
from apps.users.models import Role

from .forms import PartForm, InventoryTransactionForm, TurnoverReportFilterForm, PartRequestForm
from .models import Part, InventoryTransaction, PartRequest


class PartListView(LoginRequiredMixin, ListView):
    model = Part
    template_name = 'inventory/part_list.html'
    context_object_name = 'parts'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        low_only = self.request.GET.get('low_only')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(brand__icontains=q))
        if low_only:
            # فیلتر قطعاتی که موجودی آن‌ها کمتر از حداقل است (در پایتون محاسبه می‌شود چون
            # current_stock یک property محاسبه‌شده است، نه فیلد دیتابیس)
            qs = [p for p in qs if p.is_below_minimum]
        return qs


class PartDetailView(LoginRequiredMixin, DetailView):
    model = Part
    template_name = 'inventory/part_detail.html'
    context_object_name = 'part'


class PartCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Part
    form_class = PartForm
    template_name = 'inventory/part_form.html'
    permission_required = 'inventory.add_part'

    def form_valid(self, form):
        messages.success(self.request, 'قطعه جدید با موفقیت ثبت شد.')
        return super().form_valid(form)


class PartUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Part
    form_class = PartForm
    template_name = 'inventory/part_form.html'
    permission_required = 'inventory.change_part'

    def form_valid(self, form):
        messages.success(self.request, 'اطلاعات قطعه به‌روزرسانی شد.')
        return super().form_valid(form)


class PartDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Part
    template_name = 'inventory/part_confirm_delete.html'
    success_url = reverse_lazy('inventory:part_list')
    permission_required = 'inventory.delete_part'

    def form_valid(self, form):
        messages.success(self.request, 'قطعه حذف شد.')
        return super().form_valid(form)


class TransactionListView(LoginRequiredMixin, ListView):
    model = InventoryTransaction
    template_name = 'inventory/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('part')
        part_id = self.request.GET.get('part')
        transaction_type = self.request.GET.get('type')
        if part_id:
            qs = qs.filter(part_id=part_id)
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['parts'] = Part.objects.all()
        ctx['type_choices'] = InventoryTransaction.TransactionType.choices
        return ctx


class TransactionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = InventoryTransaction
    form_class = InventoryTransactionForm
    template_name = 'inventory/transaction_form.html'
    success_url = reverse_lazy('inventory:transaction_list')
    permission_required = 'inventory.add_inventorytransaction'

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.part.is_below_minimum:
            messages.warning(
                self.request,
                f'توجه: موجودی قطعه «{self.object.part.name}» به کمتر از حداقل رسید '
                f'({self.object.part.current_stock} < {self.object.part.min_stock}).'
            )
        else:
            messages.success(self.request, 'تراکنش انبار با موفقیت ثبت شد.')
        return response


class TurnoverReportView(LoginRequiredMixin, FormView):
    """گزارش گردش کالا در بازه زمانی دلخواه."""
    template_name = 'inventory/turnover_report.html'
    form_class = TurnoverReportFilterForm

    def get(self, request, *args, **kwargs):
        form = self.form_class(request.GET or None)
        context = self.get_report_context(form)
        return self.render_to_response(context)

    def get_report_context(self, form):
        qs = InventoryTransaction.objects.select_related('part').all()
        if form.is_valid():
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            part = form.cleaned_data.get('part')
            if date_from:
                qs = qs.filter(date__date__gte=date_from)
            if date_to:
                qs = qs.filter(date__date__lte=date_to)
            if part:
                qs = qs.filter(part=part)

        summary = list(qs.values('part__name', 'part__code').annotate(
            total_in=Sum('quantity', filter=Q(transaction_type=InventoryTransaction.TransactionType.IN)),
            total_out=Sum('quantity', filter=Q(transaction_type=InventoryTransaction.TransactionType.OUT)),
        ).order_by('part__name'))
        for row in summary:
            row['net_change'] = (row['total_in'] or 0) - (row['total_out'] or 0)

        return {'form': form, 'transactions': qs.order_by('-date'), 'summary': summary}

    def export_csv(self, request):
        form = self.form_class(request.GET or None)
        context = self.get_report_context(form)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="turnover_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['قطعه', 'کد', 'مجموع ورود', 'مجموع خروج', 'خالص گردش'])
        for row in context['summary']:
            writer.writerow([row['part__name'], row['part__code'], row['total_in'] or 0,
                              row['total_out'] or 0, row['net_change']])
        return response


def turnover_report_csv(request):
    view = TurnoverReportView()
    return view.export_csv(request)


class PartRequestCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    ثبت درخواست قطعه توسط تکنسین (معمولاً از صفحه جزئیات یک درخواست تعمیر).
    در صورت ثبت، به همه انبارداران اعلان ارسال می‌شود.
    """
    model = PartRequest
    form_class = PartRequestForm
    template_name = 'inventory/part_request_form.html'
    permission_required = 'inventory.add_partrequest'
    success_url = reverse_lazy('inventory:part_request_list')

    def get_initial(self):
        initial = super().get_initial()
        task_assignment_pk = self.request.GET.get('task_assignment')
        if task_assignment_pk:
            initial['task_assignment'] = task_assignment_pk
        return initial

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        task_assignment_pk = self.request.POST.get('task_assignment') or self.request.GET.get('task_assignment')
        if task_assignment_pk:
            form.instance.task_assignment_id = task_assignment_pk
        response = super().form_valid(form)
        notify_role(
            Role.STOREKEEPER,
            f'درخواست قطعه جدید: {self.object.quantity_requested} عدد «{self.object.part.name}» '
            f'توسط {self.request.user}',
            str(reverse_lazy('inventory:part_request_list'))
        )
        messages.success(self.request, 'درخواست قطعه ثبت و برای انباردار ارسال شد.')
        return response


class PartRequestListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    برای انباردار: لیست درخواست‌های در انتظار تامین. برای تکنسین (بدون این
    مجوز): در dashboard خودش درخواست‌های شخصی را می‌بیند، نه این لیست کلی.
    """
    model = PartRequest
    template_name = 'inventory/part_request_list.html'
    context_object_name = 'part_requests'
    permission_required = 'inventory.view_partrequest'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('part', 'requested_by', 'task_assignment')
        status = self.request.GET.get('status', PartRequest.Status.PENDING)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = PartRequest.Status.choices
        return ctx


@login_required
@transaction.atomic
def fulfill_part_request(request, pk):
    """
    تامین یک درخواست قطعه توسط انباردار: به‌صورت خودکار یک تراکنش خروج
    (InventoryTransaction) ثبت می‌شود و وضعیت درخواست «تامین‌شده» می‌شود.
    """
    if not request.user.has_perm('inventory.change_partrequest'):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    part_request = get_object_or_404(PartRequest, pk=pk, status=PartRequest.Status.PENDING)

    txn = InventoryTransaction.objects.create(
        part=part_request.part,
        transaction_type=InventoryTransaction.TransactionType.OUT,
        quantity=part_request.quantity_requested,
        reference_repair_order=part_request.task_assignment,
    )
    part_request.status = PartRequest.Status.FULFILLED
    part_request.fulfilled_transaction = txn
    part_request.save()

    notify_user(part_request.requested_by,
                f'درخواست قطعه «{part_request.part.name}» شما تامین شد.',
                str(reverse_lazy('inventory:part_request_list')))
    messages.success(request, 'درخواست تامین شد و تراکنش خروج انبار ثبت شد.')
    return redirect('inventory:part_request_list')


@login_required
def reject_part_request(request, pk):
    if not request.user.has_perm('inventory.change_partrequest'):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    part_request = get_object_or_404(PartRequest, pk=pk, status=PartRequest.Status.PENDING)
    part_request.status = PartRequest.Status.REJECTED
    part_request.save()
    notify_user(part_request.requested_by,
                f'درخواست قطعه «{part_request.part.name}» شما رد شد (موجود نیست).', '')
    messages.warning(request, 'درخواست رد شد.')
    return redirect('inventory:part_request_list')
