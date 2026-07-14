from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('export/sales.pdf', views.SalesReportPdfView.as_view(), name='sales_report_pdf'),
    path('export/sales.xlsx', views.SalesReportExcelView.as_view(), name='sales_report_excel'),
    path('export/sales.csv', views.SalesReportCsvView.as_view(), name='sales_report_csv'),
]
