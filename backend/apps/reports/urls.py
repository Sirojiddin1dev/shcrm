from django.urls import path
from .views import DashboardView, ProfitReportView, WarehouseReportView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profit/', ProfitReportView.as_view(), name='profit-report'),
    path('warehouse/', WarehouseReportView.as_view(), name='warehouse-report'),
]
