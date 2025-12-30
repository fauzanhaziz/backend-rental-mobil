from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, F # Import Q dan F untuk logic database
from decimal import Decimal

from .models import Promo
from .serializers import PromoSerializer

class PromoViewSet(viewsets.ModelViewSet):
    serializer_class = PromoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['kode', 'nama_promo']

    def get_permissions(self):
        # Hanya Admin yang boleh Create/Edit/Delete
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        user = self.request.user
        now = timezone.now() # Gunakan datetime, bukan date
        
        # 1. Admin melihat semua data
        if user.is_staff or getattr(user, 'role', '') == 'admin':
            return Promo.objects.all()
        
        # 2. Customer HANYA melihat promo yang valid & tersedia
        # Logic: Aktif AND Waktu Valid AND (Kuota Unlimited OR Kuota Belum Habis)
        return Promo.objects.filter(
            aktif=True,
            berlaku_mulai__lte=now,
            berlaku_sampai__gte=now
        ).filter(
            Q(kuota=0) | Q(sudah_digunakan__lt=F('kuota'))
        )

    @action(detail=False, methods=['get'])
    def cek_kode(self, request):
        """
        Endpoint untuk validasi kode promo di frontend.
        URL: /api/promo/cek_kode/?kode=LEBARAN&total_belanja=500000
        """
        kode = request.query_params.get('kode')
        total_belanja_str = request.query_params.get('total_belanja', '0')

        if not kode:
            return Response({"error": "Kode promo wajib diisi"}, status=400)
            
        try:
            # Case insensitive lookup
            promo = Promo.objects.get(kode__iexact=kode)
            
            # 1. Cek Validitas Dasar (Waktu, Aktif, Kuota Penuh) via Model Property
            if not promo.is_valid:
                msg = "Kode promo tidak aktif, sudah berakhir, atau kuota habis."
                return Response({"error": msg, "is_valid": False}, status=400)

            # 2. Konversi total belanja ke Decimal
            try:
                total_belanja = Decimal(total_belanja_str)
            except:
                total_belanja = Decimal(0)

            # 3. Hitung Potongan (Cek Min. Transaksi & Max Potongan)
            # Method hitung_potongan sudah menghandle logika min_transaksi
            nominal_potongan = promo.hitung_potongan(total_belanja)

            # 4. Validasi Khusus Min Transaksi
            # Jika total belanja > 0 tapi potongan 0, berarti syarat min transaksi gagal
            if total_belanja > 0 and nominal_potongan == 0:
                return Response({
                    "error": f"Minimal transaksi untuk promo ini adalah Rp {promo.min_transaksi:,.0f}",
                    "is_valid": False
                }, status=400)

            # 5. Return Data Sukses
            serializer = self.get_serializer(promo)
            return Response({
                "promo": serializer.data,
                "is_valid": True,
                "estimasi_potongan": nominal_potongan,
                "total_awal": total_belanja,
                "total_akhir": max(0, total_belanja - nominal_potongan)
            })
            
        except Promo.DoesNotExist:
            return Response({"error": "Kode promo tidak ditemukan", "is_valid": False}, status=404)