from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from apps.notifications.utils import notify_role, notify_user
from apps.users.models import Role

from .forms import (ServiceRequestForm, ServiceRequestImageFormSet, TechnicianForm,
                     TaskAssignmentForm, RepairLogForm, FieldServiceForm, CostEstimateForm)
from .models import ServiceRequest, Technician, TaskAssignment, FieldService, CostEstimate


class ServiceRequestListView(LoginRequiredMixin, ListView):
    model = ServiceRequest
    template_name = 'workshop/service_request_list.html'
    context_object_name = 'service_requests'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('customer')
        status = self.request.GET.get('status')
        q = self.request.GET.get('q')

        user = self.request.user
        # تکنسین فقط درخواست‌هایی را می‌بیند که به او تخصیص داده شده است
        if hasattr(user, 'technician_profile') and not (user.is_superuser or user.is_ceo or user.is_workshop_manager):
            qs = qs.filter(assignments__technician=user.technician_profile).distinct()

        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(machine_identifier__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = ServiceRequest.Status.choices
        return ctx


class ServiceRequestDetailView(LoginRequiredMixin, DetailView):
    model = ServiceRequest
    template_name = 'workshop/service_request_detail.html'
    context_object_name = 'service_request'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['assignment_form'] = TaskAssignmentForm()
        return ctx


@login_required
@transaction.atomic
def service_request_create_or_update(request, pk=None):
    """ثبت یا ویرایش درخواست تعمیر همراه با تصاویر (Formset)."""
    required_perm = 'workshop.change_servicerequest' if pk else 'workshop.add_servicerequest'
    if not request.user.has_perm(required_perm):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    service_request = get_object_or_404(ServiceRequest, pk=pk) if pk else None

    if request.method == 'POST':
        form = ServiceRequestForm(request.POST, instance=service_request)
        formset = ServiceRequestImageFormSet(
            request.POST, request.FILES, instance=service_request or ServiceRequest()
        )
        if form.is_valid() and formset.is_valid():
            is_new = service_request is None
            service_request = form.save()
            formset.instance = service_request
            formset.save()
            if is_new:
                notify_role(Role.WORKSHOP_MANAGER,
                            f'درخواست تعمیر جدید ثبت شد: {service_request.machine_identifier} ({service_request.customer})',
                            service_request.get_absolute_url())
            messages.success(request, 'درخواست تعمیر با موفقیت ثبت شد.')
            return redirect(service_request.get_absolute_url())
        messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = ServiceRequestForm(instance=service_request)
        formset = ServiceRequestImageFormSet(instance=service_request or ServiceRequest())

    return render(request, 'workshop/service_request_form.html', {
        'form': form, 'formset': formset, 'service_request': service_request,
    })


class ServiceRequestDeleteView(LoginRequiredMixin, DeleteView):
    model = ServiceRequest
    template_name = 'workshop/service_request_confirm_delete.html'
    success_url = '/workshop/'

    def form_valid(self, form):
        messages.success(self.request, 'درخواست تعمیر حذف شد.')
        return super().form_valid(form)


class TaskAssignmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """تخصیص یک درخواست تعمیر به یک تکنسین."""
    model = TaskAssignment
    form_class = TaskAssignmentForm
    template_name = 'workshop/assignment_form.html'
    permission_required = 'workshop.add_taskassignment'

    def form_valid(self, form):
        form.instance.service_request_id = self.kwargs['service_request_pk']
        response = super().form_valid(form)
        notify_user(
            self.object.technician.user,
            f'یک درخواست تعمیر جدید به شما محول شد: {self.object.service_request.machine_identifier}',
            self.object.service_request.get_absolute_url()
        )
        messages.success(self.request, 'تکنسین با موفقیت تخصیص داده شد.')
        return response

    def get_success_url(self):
        return self.object.service_request.get_absolute_url()


class RepairLogCreateView(LoginRequiredMixin, CreateView):
    """ثبت گزارش روزانه تعمیر توسط تکنسین."""
    model = None
    form_class = RepairLogForm
    template_name = 'workshop/repair_log_form.html'

    def dispatch(self, request, *args, **kwargs):
        from .models import RepairLog
        self.model = RepairLog
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.assignment_id = self.kwargs['assignment_pk']
        messages.success(self.request, 'گزارش تعمیر ثبت شد.')
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.assignment.service_request.get_absolute_url()


class TechnicianListView(LoginRequiredMixin, ListView):
    model = Technician
    template_name = 'workshop/technician_list.html'
    context_object_name = 'technicians'


class TechnicianCreateView(LoginRequiredMixin, CreateView):
    model = Technician
    form_class = TechnicianForm
    template_name = 'workshop/technician_form.html'
    success_url = '/workshop/technicians/'

    def form_valid(self, form):
        messages.success(self.request, 'تکنسین جدید ثبت شد.')
        return super().form_valid(form)


class FieldServiceListView(LoginRequiredMixin, ListView):
    model = FieldService
    template_name = 'workshop/field_service_list.html'
    context_object_name = 'field_services'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('service_request', 'technician')


class FieldServiceCreateView(LoginRequiredMixin, CreateView):
    model = FieldService
    form_class = FieldServiceForm
    template_name = 'workshop/field_service_form.html'
    success_url = '/workshop/field-services/'

    def form_valid(self, form):
        messages.success(self.request, 'مأموریت خارج از تعمیرگاه ثبت شد.')
        return super().form_valid(form)


class FieldServiceUpdateView(LoginRequiredMixin, UpdateView):
    model = FieldService
    form_class = FieldServiceForm
    template_name = 'workshop/field_service_form.html'
    success_url = '/workshop/field-services/'

    def form_valid(self, form):
        messages.success(self.request, 'مأموریت به‌روزرسانی شد.')
        return super().form_valid(form)


class CostEstimateCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    ثبت برآورد قیمت توسط تکنسین برای یک درخواست تعمیر مشخص. پس از ثبت، به
    همه مدیران فروش اعلان ارسال می‌شود تا برآورد را بررسی کنند.
    """
    model = CostEstimate
    form_class = CostEstimateForm
    template_name = 'workshop/cost_estimate_form.html'
    permission_required = 'workshop.add_costestimate'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['service_request'] = get_object_or_404(ServiceRequest, pk=self.kwargs['service_request_pk'])
        return ctx

    def form_valid(self, form):
        form.instance.service_request_id = self.kwargs['service_request_pk']
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        notify_role(
            Role.SALES_MANAGER,
            f'برآورد قیمت جدید برای تایید: {self.object.service_request.machine_identifier} '
            f'({self.object.estimated_cost:,.0f} ریال)',
            self.object.get_absolute_url()
        )
        messages.success(self.request, 'برآورد قیمت ثبت و برای مدیر فروش ارسال شد.')
        return response

    def get_success_url(self):
        return self.object.service_request.get_absolute_url()


class CostEstimateListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """لیست برآوردهای در انتظار تایید، برای مدیر فروش/مدیرعامل."""
    model = CostEstimate
    template_name = 'workshop/cost_estimate_list.html'
    context_object_name = 'estimates'
    permission_required = 'workshop.view_costestimate'

    def get_queryset(self):
        return CostEstimate.objects.filter(status=CostEstimate.Status.SUBMITTED).select_related(
            'service_request', 'service_request__customer', 'created_by'
        )


class CostEstimateDetailView(LoginRequiredMixin, DetailView):
    model = CostEstimate
    template_name = 'workshop/cost_estimate_detail.html'
    context_object_name = 'estimate'


@login_required
@permission_required('workshop.change_costestimate', raise_exception=True)
@transaction.atomic
def approve_cost_estimate(request, pk):
    """
    تایید برآورد قیمت توسط مدیر فروش: به‌صورت خودکار یک فرصت فروش (در صورت
    نبود) و یک پیش‌فاکتور از روی برآورد ساخته می‌شود و مدیر فروش برای
    تکمیل/ارسال آن به مشتری هدایت می‌شود.
    """
    from apps.customers.models import SalesOpportunity
    from apps.sales.models import Quote, QuoteItem

    estimate = get_object_or_404(CostEstimate, pk=pk, status=CostEstimate.Status.SUBMITTED)
    service_request = estimate.service_request

    opportunity = SalesOpportunity.objects.create(
        customer=service_request.customer,
        title=f'تعمیر: {service_request.machine_identifier} - {service_request.fault_type}',
        machine_model=service_request.machine_identifier,
        estimated_budget=estimate.estimated_cost,
        status=SalesOpportunity.Status.QUOTE_SENT,
        owner=request.user,
    )
    quote = Quote.objects.create(
        opportunity=opportunity,
        valid_until=timezone.now().date() + timedelta(days=14),
        created_by=request.user,
    )
    QuoteItem.objects.create(
        quote=quote,
        description=f'تعمیر {service_request.fault_type} ({service_request.machine_identifier})',
        quantity=1,
        unit_price=estimate.estimated_cost,
    )

    estimate.status = CostEstimate.Status.APPROVED
    estimate.reviewed_by = request.user
    estimate.reviewed_at = timezone.now()
    estimate.resulting_quote = quote
    estimate.save()

    notify_user(estimate.created_by, f'برآورد شما برای {service_request.machine_identifier} تایید و پیش‌فاکتور صادر شد.',
                quote.get_absolute_url())
    messages.success(request, 'برآورد تایید شد و پیش‌فاکتور ساخته شد؛ اکنون می‌توانید آن را تکمیل و ارسال کنید.')
    return redirect(quote.get_absolute_url())


@login_required
@permission_required('workshop.change_costestimate', raise_exception=True)
def reject_cost_estimate(request, pk):
    estimate = get_object_or_404(CostEstimate, pk=pk, status=CostEstimate.Status.SUBMITTED)
    estimate.status = CostEstimate.Status.REJECTED
    estimate.reviewed_by = request.user
    estimate.reviewed_at = timezone.now()
    estimate.save()
    notify_user(estimate.created_by, f'برآورد شما برای {estimate.service_request.machine_identifier} رد شد.',
                estimate.service_request.get_absolute_url())
    messages.warning(request, 'برآورد رد شد.')
    return redirect(estimate.service_request.get_absolute_url())
