from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
import datetime

from mobil.models import Mobil
from pesanan.models import Pesanan
from pembayaran.models import Pembayaran
from pelanggan.models import Pelanggan

class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        current_year = datetime.datetime.now().year

        # 1. Total Stats
        total_mobil = Mobil.objects.count()
        total_pesanan = Pesanan.objects.count()
        pembayaran_lunas = Pembayaran.objects.filter(status='lunas').count()
        total_pelanggan = Pelanggan.objects.count()

        # 2. Revenue Chart
        revenue_chart = Pembayaran.objects.filter(
            status='lunas',
            created_at__year=current_year
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('jumlah')
        ).order_by('month')

        # 3. Orders Chart
        orders_chart = Pesanan.objects.filter(
            created_at__year=current_year
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            orders=Count('id')
        ).order_by('month')

        # 4. Recent Activities (UPDATE CORPORATE LOGIC)
        recent_orders = Pesanan.objects.select_related('pelanggan', 'mobil').order_by('-created_at')[:5]
        activities = []
        
        for order in recent_orders:
            # LOGIKA BARU: Cek apakah ini Corporate atau Personal
            if order.is_corporate and order.perusahaan_nama:
                display_name = f"{order.perusahaan_nama} (Corporate)"
            elif order.pelanggan:
                display_name = order.pelanggan.nama
            else:
                display_name = "Guest"

            activities.append({
                'id': order.id,
                'customer': display_name,  # Nama yang muncul di Dashboard
                'action': f"menyewa {order.mobil.nama_mobil}",
                'time': order.created_at
            })

        # Formatting Chart Data
        chart_data = self._format_chart_data(revenue_chart, orders_chart)

        return Response({
            'stats': {
                'total_mobil': total_mobil,
                'total_pesanan': total_pesanan,
                'pembayaran_lunas': pembayaran_lunas,
                'total_pelanggan': total_pelanggan,
            },
            'charts': chart_data,
            'recent_activities': activities
        })

    def _format_chart_data(self, revenue_qs, orders_qs):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        data = []
        for i in range(12):
            data.append({'month': months[i], 'revenue': 0, 'orders': 0})

        for r in revenue_qs:
            if r['month']:
                idx = r['month'].month - 1
                data[idx]['revenue'] = r['revenue']

        for o in orders_qs:
            if o['month']:
                idx = o['month'].month - 1
                data[idx]['orders'] = o['orders']
            
        return data