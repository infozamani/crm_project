from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, DeleteView

from apps.notifications.utils import notify_user

from .forms import QuoteForm, QuoteItemFormSet, ContractForm, CheckFormSet, DeliveryScheduleFormSet
from .models import Quote, Contract


class QuoteListView(LoginRequiredMixin, ListView):
    model = Quote
    template_name = 'sales/quote_list.html'
    context_object_name = 'quotes'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('opportunity', 'opportunity__customer')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(number__icontains=q)
        return qs


class QuoteDetailView(LoginRequiredMixin, DetailView):
    model = Quote
    template_name = 'sales/quote_detail.html'
    context_object_name = 'quote'


class SendQuoteToCustomerView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    ارسال پیش‌فاکتور به مشتری: وضعیت را «ارسال‌شده» می‌کند و اگر مشتری حساب
    پرتال داشته باشد، یک اعلان برایش می‌فرستد تا آن را در پرتال خودش ببیند
    و تایید/رد کند.
    """
    permission_required = 'sales.change_quote'

    def post(self, request, pk):
        quote = get_object_or_404(Quote, pk=pk)
        quote.status = Quote.Status.SENT
        quote.sent_at = timezone.now()
        quote.save(update_fields=['status', 'sent_at'])

        customer = quote.opportunity.customer
        if customer.portal_user_id:
            notify_user(
                customer.portal_user,
                f'پیش‌فاکتور جدید «{quote.number}» برای شما ارسال شد. لطفاً بررسی و تایید کنید.',
                quote.get_portal_absolute_url(),
            )
            messages.success(request, 'پیش‌فاکتور ارسال شد و مشتری اعلان دریافت کرد.')
        else:
            messages.warning(
                request,
                'پیش‌فاکتور به‌عنوان «ارسال‌شده» علامت خورد، اما این مشتری هنوز حساب پرتال ندارد؛ '
                'از صفحه مشتری یک حساب پرتال برایش بسازید تا بتواند آن را ببیند.'
            )
        return redirect(quote.get_absolute_url())


@login_required
@transaction.atomic
def quote_create_or_update(request, pk=None):
    """ثبت یا ویرایش پیش‌فاکتور همراه با آیتم‌ها (Formset)."""
    required_perm = 'sales.change_quote' if pk else 'sales.add_quote'
    if not request.user.has_perm(required_perm):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    quote = get_object_or_404(Quote, pk=pk) if pk else None

    if request.method == 'POST':
        form = QuoteForm(request.POST, instance=quote)
        formset = QuoteItemFormSet(request.POST, instance=quote or Quote())
        if form.is_valid() and formset.is_valid():
            quote = form.save(commit=False)
            if not quote.created_by_id:
                quote.created_by = request.user
            quote.save()
            formset.instance = quote
            formset.save()
            messages.success(request, 'پیش‌فاکتور با موفقیت ثبت شد.')
            return redirect(quote.get_absolute_url())
        messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = QuoteForm(instance=quote)
        formset = QuoteItemFormSet(instance=quote or Quote())

    return render(request, 'sales/quote_form.html', {'form': form, 'formset': formset, 'quote': quote})


class QuoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Quote
    template_name = 'sales/quote_confirm_delete.html'
    success_url = '/sales/quotes/'

    def form_valid(self, form):
        messages.success(self.request, 'پیش‌فاکتور حذف شد.')
        return super().form_valid(form)


class ContractListView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'sales/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('customer')
        status = self.request.GET.get('status')
        contract_type = self.request.GET.get('type')
        if status:
            qs = qs.filter(status=status)
        if contract_type:
            qs = qs.filter(contract_type=contract_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Contract.Status.choices
        ctx['type_choices'] = Contract.ContractType.choices
        return ctx


class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'sales/contract_detail.html'
    context_object_name = 'contract'


@login_required
@transaction.atomic
def contract_create_or_update(request, pk=None):
    """ثبت یا ویرایش قرارداد همراه با چک‌ها و مراحل تحویل (Formsets)."""
    required_perm = 'sales.change_contract' if pk else 'sales.add_contract'
    if not request.user.has_perm(required_perm):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    contract = get_object_or_404(Contract, pk=pk) if pk else None

    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, instance=contract)
        check_formset = CheckFormSet(request.POST, instance=contract or Contract(), prefix='checks')
        delivery_formset = DeliveryScheduleFormSet(request.POST, instance=contract or Contract(), prefix='delivery')

        if form.is_valid() and check_formset.is_valid() and delivery_formset.is_valid():
            contract = form.save(commit=False)
            if not contract.created_by_id:
                contract.created_by = request.user
            contract.full_clean()
            contract.save()
            check_formset.instance = contract
            check_formset.save()
            delivery_formset.instance = contract
            delivery_formset.save()
            messages.success(request, 'قرارداد با موفقیت ثبت شد.')
            return redirect(contract.get_absolute_url())
        messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        initial = {}
        quote_id = request.GET.get('quote')
        if not contract and quote_id:
            from .models import Quote as QuoteModel
            source_quote = QuoteModel.objects.filter(pk=quote_id).select_related('opportunity__customer').first()
            if source_quote:
                initial = {
                    'customer': source_quote.opportunity.customer_id,
                    'quote': source_quote.id,
                    # مبلغ پیش‌فاکتور اعشار دارد (برای محاسبه دقیق تخفیف/مالیات)؛
                    # چون فیلد قرارداد ریال صحیح است، اینجا به نزدیک‌ترین ریال گرد می‌شود.
                    'total_amount': round(source_quote.total_amount),
                }
        form = ContractForm(instance=contract, initial=initial)
        check_formset = CheckFormSet(instance=contract or Contract(), prefix='checks')
        delivery_formset = DeliveryScheduleFormSet(instance=contract or Contract(), prefix='delivery')

    return render(request, 'sales/contract_form.html', {
        'form': form, 'check_formset': check_formset,
        'delivery_formset': delivery_formset, 'contract': contract,
    })


class ContractDeleteView(LoginRequiredMixin, DeleteView):
    model = Contract
    template_name = 'sales/contract_confirm_delete.html'
    success_url = '/sales/contracts/'

    def form_valid(self, form):
        messages.success(self.request, 'قرارداد حذف شد.')
        return super().form_valid(form)
