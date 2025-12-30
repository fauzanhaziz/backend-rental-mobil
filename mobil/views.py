from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Mobil
from .serializers import MobilSerializer, MobilListSerializer
from pesanan.models import Pesanan # Import Model Pesanan untuk cek ketersediaan

class MobilViewSet(viewsets.ModelViewSet):
    queryset = Mobil.objects.all()
    # Orang umum boleh LIHAT, tapi hanya Admin (Authenticated) yang boleh EDIT
    permission_classes = [IsAuthenticatedOrReadOnly]
    # Mendukung upload file gambar
    parser_classes = [MultiPartParser, FormParser]
    
    # Search & Order bawaan DRF
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nama_mobil', 'merk', 'plat_nomor']
    ordering_fields = ['harga_per_hari', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MobilListSerializer
        return MobilSerializer
    
    def get_queryset(self):
        """
        Custom Filtering yang Powerful untuk Frontend
        """
        queryset = Mobil.objects.all()
        user = self.request.user
        
        # 1. Logika Status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        else:
            # Jika bukan admin, hanya tampilkan yang aktif
            if not (user.is_authenticated and (user.is_staff or getattr(user, 'role', '') == 'admin')):
                queryset = queryset.filter(status='aktif')
        
        # 2. Filter Merk
        merk = self.request.query_params.get('merk')
        if merk:
            queryset = queryset.filter(merk__icontains=merk)

        # 3. Filter Transmisi
        transmisi = self.request.query_params.get('transmisi')
        if transmisi:
            queryset = queryset.filter(transmisi=transmisi)

        # 4. Filter Kapasitas Kursi
        min_kursi = self.request.query_params.get('min_kursi')
        if min_kursi:
            queryset = queryset.filter(kapasitas_kursi__gte=min_kursi)
            
        # 5. Filter Range Harga
        min_harga = self.request.query_params.get('min_harga')
        max_harga = self.request.query_params.get('max_harga')
        if min_harga:
            queryset = queryset.filter(harga_per_hari__gte=min_harga)
        if max_harga:
            queryset = queryset.filter(harga_per_hari__lte=max_harga)

        # 6. Filter Popularitas
        popularity = self.request.query_params.get('popularity')
        if popularity:
            queryset = queryset.filter(popularity=popularity)
        
        # 7. Filter Dengan Supir
        dengan_supir = self.request.query_params.get('dengan_supir')
        if dengan_supir is not None:
            is_supir = dengan_supir.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(dengan_supir=is_supir)

        return queryset

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def rekomendasi(self, request):
        """
        API untuk menampilkan 'Mobil Pilihan' di Homepage
        """
        mobil_aktif = Mobil.objects.filter(status='aktif')
        
        rekomendasi = mobil_aktif.exclude(popularity='standard').order_by('-created_at')[:6]
        
        if rekomendasi.count() < 12:
            sisa_slot = 12 - rekomendasi.count()
            standar = mobil_aktif.filter(popularity='standard').order_by('-created_at')[:sisa_slot]
            from itertools import chain
            hasil_akhir = list(chain(rekomendasi, standar))
        else:
            hasil_akhir = rekomendasi

        serializer = MobilListSerializer(hasil_akhir, many=True, context={'request': request})
        return Response(serializer.data)

    # --- ACTION BARU: CEK TANGGAL YANG SUDAH DIBOOKING ---
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def unavailable_dates(self, request, pk=None):
        mobil = self.get_object()
        today = timezone.now().date()
        
        # LOGIKA CERDAS:
        # Pesanan dianggap "memblokir" jadwal HANYA JIKA:
        # 1. Statusnya 'lunas'/'aktif' DAN Tanggal Selesainya >= HARI INI
        # 2. (Artinya pesanan aktif yang tanggal selesainya KEMARIN, tidak dianggap memblokir)
        
        from django.db.models import Q
        
        bookings = Pesanan.objects.filter(
            mobil=mobil
        ).filter(
            # Blokir jika status Konfirmasi/Pending yang valid
            (Q(status__in=['pending', 'konfirmasi']) & Q(tanggal_mulai__gte=today)) |
            
            # Blokir jika status Aktif TAPI masa sewanya belum habis (atau habis hari ini)
            (Q(status__in=['lunas', 'sedang_disewa', 'aktif']) & Q(tanggal_selesai__gte=today))
        ).values('tanggal_mulai', 'tanggal_selesai')
        
        return Response(list(bookings))