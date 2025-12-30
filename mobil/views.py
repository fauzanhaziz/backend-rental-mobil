from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone # Pastikan import ini ada

from .models import Mobil
from .serializers import MobilSerializer, MobilListSerializer
from pesanan.models import Pesanan 

class MobilViewSet(viewsets.ModelViewSet):
    queryset = Mobil.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nama_mobil', 'merk', 'plat_nomor']
    ordering_fields = ['harga_per_hari', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MobilListSerializer
        return MobilSerializer
    
    def get_queryset(self):
        queryset = Mobil.objects.all()
        user = self.request.user
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        else:
            if not (user.is_authenticated and (user.is_staff or getattr(user, 'role', '') == 'admin')):
                queryset = queryset.filter(status='aktif')
        
        merk = self.request.query_params.get('merk')
        if merk:
            queryset = queryset.filter(merk__icontains=merk)

        transmisi = self.request.query_params.get('transmisi')
        if transmisi:
            queryset = queryset.filter(transmisi=transmisi)

        min_kursi = self.request.query_params.get('min_kursi')
        if min_kursi:
            queryset = queryset.filter(kapasitas_kursi__gte=min_kursi)
            
        min_harga = self.request.query_params.get('min_harga')
        max_harga = self.request.query_params.get('max_harga')
        if min_harga:
            queryset = queryset.filter(harga_per_hari__gte=min_harga)
        if max_harga:
            queryset = queryset.filter(harga_per_hari__lte=max_harga)

        popularity = self.request.query_params.get('popularity')
        if popularity:
            queryset = queryset.filter(popularity=popularity)
        
        dengan_supir = self.request.query_params.get('dengan_supir')
        if dengan_supir is not None:
            is_supir = dengan_supir.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(dengan_supir=is_supir)

        return queryset

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def rekomendasi(self, request):
        mobil_aktif = Mobil.objects.filter(status='aktif')
        
        # Ambil mobil selain standard
        rekomendasi_qs = mobil_aktif.exclude(popularity='standard').order_by('-created_at')[:6]
        
        hasil_akhir = list(rekomendasi_qs)
        if len(hasil_akhir) < 12:
            sisa_slot = 12 - len(hasil_akhir)
            standar = mobil_aktif.filter(popularity='standard').order_by('-created_at')[:sisa_slot]
            hasil_akhir.extend(list(standar))

        # PENTING: Sertakan context agar URL gambar Cloudinary diproses sempurna
        serializer = MobilListSerializer(hasil_akhir, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def unavailable_dates(self, request, pk=None):
        mobil = self.get_object()
        today = timezone.now().date()
        
        from django.db.models import Q
        
        bookings = Pesanan.objects.filter(
            mobil=mobil
        ).filter(
            (Q(status__in=['pending', 'konfirmasi']) & Q(tanggal_mulai__gte=today)) |
            (Q(status__in=['lunas', 'sedang_disewa', 'aktif']) & Q(tanggal_selesai__gte=today))
        ).values('tanggal_mulai', 'tanggal_selesai')
        
        return Response(list(bookings))