from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, TemplateView

from apps.notifications.utils import notify_role, notify_user
from apps.sales.models import Quote, Contract
from apps.users.models import Role
from apps.workshop.models import ServiceRequest

from .forms import PortalServiceRequestForm, PortalServiceRequestMediaFormSet, ServiceRequestRatingForm
from .mixins import CustomerRequiredMixin


class PortalDashboardView(CustomerRequiredMixin, TemplateView):
    """
    داشبورد پرتال مشتری: خلاصه‌ای از وضعیت درخواست‌های تعمیر، پیش‌فاکتورها و
    قراردادهای فعال مشتری، بدون هیچ اطلاعات داخلی سازمان (فقط داده‌های خود او).
    یادآوری‌های برجسته برای «رضایت‌سنجی ثبت‌نشده» و «پیش‌فاکتور/قرارداد در
    انتظار تایید» نیز اینجا نمایش داده می‌شود.
    """
    template_name = 'portal/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        customer = self.request.user.customer_record
        ctx['customer'] = customer
        ctx['open_service_requests'] = ServiceRequest.objects.filter(customer=customer).exclude(
            status=ServiceRequest.Status.DELIVERED
        ).order_by('-received_at')[:5]
        ctx['recent_quotes'] = Quote.objects.filter(
            opportunity__customer=customer
        ).order_by('-created_at')[:5]
        ctx['active_contracts'] = Contract.objects.filter(
            customer=customer, status=Contract.Status.ACTIVE
        )
        ctx['unrated_requests'] = ServiceRequest.objects.filter(
            customer=customer, status=ServiceRequest.Status.DELIVERED, customer_rating__isnull=True
        )
        ctx['pending_quotes'] = Quote.objects.filter(
            opportunity__customer=customer, status=Quote.Status.SENT
        )
        ctx['pending_contracts'] = Contract.objects.filter(
            customer=customer, is_confirmed_by_customer=False
        )
        return ctx


class PortalServiceRequestListView(CustomerRequiredMixin, ListView):
    """تاریخچه کامل درخواست‌های تعمیر مشتری."""
    model = ServiceRequest
    template_name = 'portal/service_request_list.html'
    context_object_name = 'service_requests'
    paginate_by = 15

    def get_queryset(self):
        customer = self.request.user.customer_record
        return ServiceRequest.objects.filter(customer=customer).order_by('-received_at')


class PortalServiceRequestDetailView(CustomerRequiredMixin, DetailView):
    """
    پیگیری روند تعمیر یک دستگاه خاص: وضعیت فعلی، تکنسین مسئول (در صورت
    تخصیص) و گزارش‌های تعمیر ثبت‌شده، به‌صورت یک جدول زمانی ساده. اگر دستگاه
    تحویل داده شده و هنوز رضایت‌سنجی ثبت نشده، فرم امتیازدهی هم اینجا نشان
    داده می‌شود.
    """
    model = ServiceRequest
    template_name = 'portal/service_request_detail.html'
    context_object_name = 'service_request'

    def get_queryset(self):
        # مشتری فقط اجازه دیدن درخواست‌های خودش را دارد
        return ServiceRequest.objects.filter(customer=self.request.user.customer_record)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['assignments'] = self.object.assignments.select_related('technician__user').prefetch_related('repair_logs')
        ctx['media_items'] = self.object.customer_media.all()
        if self.object.needs_rating:
            ctx['rating_form'] = ServiceRequestRatingForm(instance=self.object)
        return ctx


class PortalServiceRequestCreateView(CustomerRequiredMixin, CreateView):
    """
    ثبت درخواست تعمیر جدید توسط خود مشتری، همراه با حداقل یک عکس یا فیلم از
    خرابی (الزامی، چون توضیح متنی به‌تنهایی برای تشخیص تکنسین کافی نیست).
    """
    model = ServiceRequest
    form_class = PortalServiceRequestForm
    template_name = 'portal/service_request_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if 'media_formset' not in ctx:
            ctx['media_formset'] = PortalServiceRequestMediaFormSet(
                self.request.POST or None, self.request.FILES or None, instance=ServiceRequest()
            )
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        media_formset = PortalServiceRequestMediaFormSet(
            request.POST, request.FILES, instance=ServiceRequest()
        )
        if form.is_valid() and media_formset.is_valid():
            service_request = form.save(commit=False)
            service_request.customer = request.user.customer_record
            service_request.save()
            media_formset.instance = service_request
            media_formset.save()
            messages.success(request, 'درخواست تعمیر شما همراه با تصاویر/فیلم ارسال‌شده با موفقیت ثبت شد.')
            return redirect(service_request.get_portal_absolute_url())
        messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید؛ ارسال حداقل یک عکس یا فیلم از خرابی الزامی است.')
        return self.render_to_response(self.get_context_data(form=form, media_formset=media_formset))


class PortalRateServiceRequestView(CustomerRequiredMixin, View):
    """ثبت رضایت‌سنجی (۱ تا ۵ ستاره) پس از تحویل دستگاه."""

    def post(self, request, pk):
        service_request = get_object_or_404(
            ServiceRequest, pk=pk, customer=request.user.customer_record
        )
        form = ServiceRequestRatingForm(request.POST, instance=service_request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.rated_at = timezone.now()
            obj.save(update_fields=['customer_rating', 'customer_feedback', 'rated_at'])
            messages.success(request, 'از بازخورد شما سپاسگزاریم! 🙏')
        else:
            messages.error(request, 'لطفاً امتیاز خود را انتخاب کنید.')
        return redirect(service_request.get_portal_absolute_url())


class PortalQuoteListView(CustomerRequiredMixin, ListView):
    """پیش‌فاکتورهای مربوط به مشتری."""
    model = Quote
    template_name = 'portal/quote_list.html'
    context_object_name = 'quotes'
    paginate_by = 15

    def get_queryset(self):
        customer = self.request.user.customer_record
        return Quote.objects.filter(opportunity__customer=customer).select_related('opportunity').order_by('-created_at')


class PortalQuoteDetailView(CustomerRequiredMixin, DetailView):
    """جزئیات یک پیش‌فاکتور خاص برای مشتری، همراه با دکمه تایید/رد در صورتی
    که پیش‌فاکتور ارسال‌شده و هنوز پاسخ داده نشده باشد."""
    model = Quote
    template_name = 'portal/quote_detail.html'
    context_object_name = 'quote'

    def get_queryset(self):
        customer = self.request.user.customer_record
        return Quote.objects.filter(opportunity__customer=customer)


class PortalQuoteRespondView(CustomerRequiredMixin, View):
    """تایید یا رد پیش‌فاکتور توسط مشتری؛ در هر دو حالت به کارشناس/مدیر فروش اعلان می‌رود."""

    def post(self, request, pk):
        quote = get_object_or_404(
            Quote, pk=pk, opportunity__customer=request.user.customer_record, status=Quote.Status.SENT
        )
        decision = request.POST.get('decision')
        quote.customer_responded_at = timezone.now()
        if decision == 'approve':
            quote.status = Quote.Status.APPROVED
            messages.success(request, 'پیش‌فاکتور با موفقیت تایید شد. کارشناس فروش قرارداد را برای شما آماده می‌کند.')
        else:
            quote.status = Quote.Status.REJECTED
            messages.info(request, 'پیش‌فاکتور رد شد. کارشناس فروش با شما تماس خواهد گرفت.')
        quote.save(update_fields=['status', 'customer_responded_at'])

        recipient = quote.created_by or quote.opportunity.owner
        if recipient:
            verb = 'تایید' if decision == 'approve' else 'رد'
            notify_user(recipient, f'مشتری پیش‌فاکتور «{quote.number}» را {verb} کرد.', quote.get_absolute_url())
        return redirect(quote.get_portal_absolute_url())


class PortalContractListView(CustomerRequiredMixin, ListView):
    """قراردادهای مشتری (فقط مشاهده)."""
    model = Contract
    template_name = 'portal/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 15

    def get_queryset(self):
        customer = self.request.user.customer_record
        return Contract.objects.filter(customer=customer).order_by('-signed_date')


class PortalContractDetailView(CustomerRequiredMixin, DetailView):
    """جزئیات یک قرارداد برای مشتری، همراه با دکمه «تایید و شروع کار»."""
    model = Contract
    template_name = 'portal/contract_detail.html'
    context_object_name = 'contract'

    def get_queryset(self):
        customer = self.request.user.customer_record
        return Contract.objects.filter(customer=customer)


class PortalContractConfirmView(CustomerRequiredMixin, View):
    """
    تایید قرارداد توسط مشتری. این کار به مدیر فروش/مدیر تعمیرگاه اعلان
    می‌فرستد که «مشتری قرارداد را تایید کرد، کار تعمیر می‌تواند شروع شود».
    """

    def post(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk, customer=request.user.customer_record)
        if not contract.is_confirmed_by_customer:
            contract.is_confirmed_by_customer = True
            contract.confirmed_at = timezone.now()
            contract.save(update_fields=['is_confirmed_by_customer', 'confirmed_at'])
            notify_role(
                Role.WORKSHOP_MANAGER,
                f'مشتری قرارداد شماره {contract.pk} را تایید کرد؛ کار تعمیر می‌تواند شروع شود.',
                contract.get_absolute_url(),
            )
            if contract.created_by:
                notify_user(
                    contract.created_by,
                    f'مشتری قرارداد شماره {contract.pk} را تایید کرد.',
                    contract.get_absolute_url(),
                )
            messages.success(request, 'قرارداد تایید شد. تیم تعمیرگاه مطلع شد و کار آغاز خواهد شد. ✅')
        return redirect('portal:contract_detail', pk=contract.pk)
