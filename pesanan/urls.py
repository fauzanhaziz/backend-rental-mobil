from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PesananViewSet
from .views_report import DashboardReportView
from .views_dashboard import AdminDashboardStatsView 

router = DefaultRouter()
router.register(r'', PesananViewSet)

urlpatterns = [
    # Endpoint untuk Dashboard Utama (Card Stats & Chart)
    # URL: /api/pesanan/dashboard/stats/
    path('dashboard/stats/', AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),

    # Endpoint untuk Laporan Lengkap (PDF/Excel)
    # URL: /api/pesanan/reports/dashboard/
    path('reports/dashboard/', DashboardReportView.as_view(), name='dashboard-report'),
    
    # Endpoint CRUD Pesanan (Bawaan Router)
    path('', include(router.urls)),
]