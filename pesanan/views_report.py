# backend/pesanan/views.py (Tambahkan ini)

from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .models import Pesanan
from pembayaran.models import Pembayaran

class DashboardReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 1. Total Pesanan & Revenue per Bulan (Tahun berjalan)
        import datetime
        current_year = datetime.datetime.now().year
        
        # Agregasi Pesanan per Bulan
        orders_per_month = Pesanan.objects.filter(
            created_at__year=current_year
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_orders=Count('id')
        ).order_by('month')

        # Agregasi Revenue per Bulan (Hanya yang Lunas)
        revenue_per_month = Pembayaran.objects.filter(
            status='lunas',
            created_at__year=current_year
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_revenue=Sum('jumlah')
        ).order_by('month')

        # 2. Distribusi Tipe Mobil
        car_types = Pesanan.objects.filter(
            status__in=['konfirmasi', 'selesai']
        ).values('mobil__jenis').annotate(
            count=Count('id')
        ).order_by('-count')

        # Formatting Data untuk Frontend
        months_label = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Init data kosong
        report_data = {
            'orders': [{'month': m, 'orders': 0} for m in months_label],
            'revenue': [{'month': m, 'revenue': 0} for m in months_label],
            'car_types': []
        }

        # Isi data Orders
        for item in orders_per_month:
            m_index = item['month'].month - 1
            report_data['orders'][m_index]['orders'] = item['total_orders']

        # Isi data Revenue
        for item in revenue_per_month:
            m_index = item['month'].month - 1
            report_data['revenue'][m_index]['revenue'] = item['total_revenue']

        # Isi data Car Types
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899']
        for idx, item in enumerate(car_types):
            report_data['car_types'].append({
                'name': item['mobil__jenis'] or 'Lainnya',
                'value': item['count'],
                'color': colors[idx % len(colors)]
            })

        return Response(report_data)