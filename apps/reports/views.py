import csv
import io
from datetime import date, timedelta

import jdatetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Avg
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic import TemplateView, View

from apps.customers.models import SalesOpportunity
from apps.sales.models import Contract
from apps.workshop.models import ServiceRequest, RepairLog, CostEstimate
from apps.inventory.models import InventoryTransaction, PartRequest

MONTH_LABELS_FA = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']


def _current_jalali_year_gregorian_range():
    """بازه تاریخ میلادی متناظر با سال شمسی جاری (برای فیلتر کوئری‌ها)."""
    jy = jdatetime.date.today().year
    start = jdatetime.date(jy, 1, 1).togregorian()
    end = jdatetime.date(jy + 1, 1, 1).togregorian() - timedelta(days=1)
    return jy, start, end


def _build_sales_widgets(user):
    """کارت‌ها/نمودارهای مرتبط با فروش و قراردادها (فقط برای نقش‌های مرتبط)."""
    jalali_year, start_g, end_g = _current_jalali_year_gregorian_range()

    is_manager_scope = user.is_ceo or user.is_sales_manager
    opp_qs = SalesOpportunity.objects.exclude(
        status__in=[SalesOpportunity.Status.CLOSED_WON, SalesOpportunity.Status.CANCELLED]
    )
    if not is_manager_scope:
        opp_qs = opp_qs.filter(owner=user)

    contract_qs = Contract.objects.filter(signed_date__gte=start_g, signed_date__lte=end_g)
    yearly_contract_total = contract_qs.aggregate(total=Sum('total_amount'))['total'] or 0

    monthly_totals = [0.0] * 12
    for c in contract_qs.only('signed_date', 'total_amount'):
        jd = jdatetime.date.fromgregorian(date=c.signed_date)
        monthly_totals[jd.month - 1] += float(c.total_amount)

    return {
        'open_opportunities_count': opp_qs.count(),
        'active_contracts_count': Contract.objects.filter(status=Contract.Status.ACTIVE).count(),
        'yearly_contract_total': yearly_contract_total,
        'jalali_year': jalali_year,
        'monthly_sales_labels': MONTH_LABELS_FA,
        'monthly_sales_values': monthly_totals,
        'pending_estimates_count': CostEstimate.objects.filter(status=CostEstimate.Status.SUBMITTED).count(),
    }


def _build_workshop_widgets(user):
    """کارت‌ها/نمودارهای مرتبط با تعمیرگاه."""
    status_display_map = dict(ServiceRequest.Status.choices)
    repair_status_qs = ServiceRequest.objects.values('status').annotate(count=Count('id'))

    top_tech_qs = (
        RepairLog.objects.values('assignment__technician__user__first_name',
                                  'assignment__technician__user__last_name')
        .annotate(total_hours=Sum('hours_spent'))
        .order_by('-total_hours')[:5]
    )

    rated_qs = ServiceRequest.objects.filter(customer_rating__isnull=False)
    avg_rating = rated_qs.aggregate(avg=Avg('customer_rating'))['avg']

    return {
        'open_service_requests_count': ServiceRequest.objects.exclude(
            status=ServiceRequest.Status.DELIVERED
        ).count(),
        'repair_status_labels': [status_display_map.get(row['status'], row['status']) for row in repair_status_qs],
        'repair_status_values': [row['count'] for row in repair_status_qs],
        'top_technicians_labels': [
            (f"{row['assignment__technician__user__first_name']} "
             f"{row['assignment__technician__user__last_name']}").strip() or 'نامشخص'
            for row in top_tech_qs
        ],
        'top_technicians_values': [float(row['total_hours'] or 0) for row in top_tech_qs],
        'pending_part_requests_count': PartRequest.objects.filter(status=PartRequest.Status.PENDING).count(),
        'avg_customer_rating': round(avg_rating, 1) if avg_rating else None,
        'rated_requests_count': rated_qs.count(),
    }


def _build_inventory_widgets(user):
    """کارت‌ها/نمودارهای مرتبط با انبار."""
    from apps.inventory.models import Part

    parts_qs = (
        InventoryTransaction.objects.filter(transaction_type=InventoryTransaction.TransactionType.OUT)
        .values('part__name')
        .annotate(total_out=Sum('quantity'))
        .order_by('-total_out')[:5]
    )
    low_stock_parts = [p for p in Part.objects.all() if p.is_below_minimum]

    return {
        'parts_consumption_labels': [row['part__name'] for row in parts_qs],
        'parts_consumption_values': [row['total_out'] for row in parts_qs],
        'low_stock_parts': low_stock_parts,
        'pending_part_requests_count': PartRequest.objects.filter(status=PartRequest.Status.PENDING).count(),
    }


def _build_my_tasks_widget(user):
    """برای تکنسین: فقط کارهای محول‌شده به خودش (بدون هیچ اطلاعات مالی)."""
    if not hasattr(user, 'technician_profile'):
        return {'my_open_assignments': [], 'my_pending_part_requests': []}
    tech = user.technician_profile
    from apps.workshop.models import TaskAssignment
    return {
        'my_open_assignments': TaskAssignment.objects.filter(
            technician=tech, end_date__isnull=True
        ).select_related('service_request', 'service_request__customer'),
        'my_pending_part_requests': PartRequest.objects.filter(
            requested_by=user
        ).exclude(status=PartRequest.Status.FULFILLED).select_related('part')[:10],
    }


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    داشبورد مدیریتی نقش‌محور: هر کاربر فقط کارت‌ها/نمودارهای مرتبط با نقش
    خودش را می‌بیند (با استفاده از سیستم مجوزهای Django که در setup_groups
    تعریف شده است)، نه کل اطلاعات سازمان را.
    """
    template_name = 'reports/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        widgets = {
            'sales': user.has_perm('customers.view_salesopportunity') or user.has_perm('sales.view_contract'),
            'workshop': user.has_perm('workshop.view_servicerequest'),
            'inventory': user.has_perm('inventory.view_inventorytransaction') or user.is_storekeeper,
            'my_tasks': user.is_technician,
            'exports': user.has_perm('sales.view_contract'),
        }
        ctx['widgets'] = widgets

        if widgets['sales']:
            ctx.update(_build_sales_widgets(user))
        if widgets['workshop']:
            ctx.update(_build_workshop_widgets(user))
        if widgets['inventory']:
            ctx.update(_build_inventory_widgets(user))
        if widgets['my_tasks']:
            ctx.update(_build_my_tasks_widget(user))

        import json
        for key in ('monthly_sales_labels', 'monthly_sales_values', 'repair_status_labels',
                    'repair_status_values', 'top_technicians_labels', 'top_technicians_values',
                    'parts_consumption_labels', 'parts_consumption_values'):
            if key in ctx:
                ctx[f'{key}_json'] = json.dumps(ctx[key], ensure_ascii=False)
        return ctx


class SalesReportPdfView(LoginRequiredMixin, View):
    """خروجی PDF از گزارش خلاصه فروش و قراردادها با xhtml2pdf."""

    def get(self, request, *args, **kwargs):
        from xhtml2pdf import pisa

        contracts = Contract.objects.select_related('customer').order_by('-signed_date')[:200]
        html = render_to_string('reports/sales_report_pdf.html', {
            'contracts': contracts,
            'generated_at': timezone.now(),
            'total': contracts.aggregate(total=Sum('total_amount'))['total'] or 0,
        })
        result = io.BytesIO()
        pisa_status = pisa.CreatePDF(src=html, dest=result, encoding='utf-8')
        if pisa_status.err:
            return HttpResponse('خطا در تولید PDF', status=500)
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{date.today()}.pdf"'
        return response


class SalesReportExcelView(LoginRequiredMixin, View):
    """خروجی Excel از گزارش خلاصه فروش و قراردادها با openpyxl."""

    def get(self, request, *args, **kwargs):
        from openpyxl import Workbook
        from openpyxl.styles import Font

        wb = Workbook()
        ws = wb.active
        ws.title = 'گزارش قراردادها'
        headers = ['مشتری', 'نوع قرارداد', 'تاریخ امضا', 'مبلغ کل', 'پیش‌پرداخت', 'وضعیت']
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        contracts = Contract.objects.select_related('customer').order_by('-signed_date')
        for c in contracts:
            ws.append([
                str(c.customer), c.get_contract_type_display(), c.signed_date.isoformat(),
                float(c.total_amount), float(c.down_payment), c.get_status_display(),
            ])

        for column_cells in ws.columns:
            length = max(len(str(cell.value)) for cell in column_cells if cell.value is not None) if any(
                cell.value for cell in column_cells) else 10
            ws.column_dimensions[column_cells[0].column_letter].width = min(length + 4, 40)

        buffer = io.BytesIO()
        wb.save(buffer)
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="sales_report_{date.today()}.xlsx"'
        return response


class SalesReportCsvView(LoginRequiredMixin, View):
    """خروجی CSV از گزارش خلاصه فروش و قراردادها."""

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{date.today()}.csv"'
        writer = csv.writer(response)
        writer.writerow(['مشتری', 'نوع قرارداد', 'تاریخ امضا', 'مبلغ کل', 'پیش‌پرداخت', 'وضعیت'])
        for c in Contract.objects.select_related('customer').order_by('-signed_date'):
            writer.writerow([str(c.customer), c.get_contract_type_display(), c.signed_date.isoformat(),
                              c.total_amount, c.down_payment, c.get_status_display()])
        return response
