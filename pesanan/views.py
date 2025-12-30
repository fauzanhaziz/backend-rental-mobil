from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from .models import Pesanan
from mobil.models import Mobil
from mobil.serializers import MobilSerializer
from .serializers import PesananSerializer, CreatePesananSerializer, AdminCreatePesananSerializer

class PesananViewSet(viewsets.ModelViewSet):
    queryset = Pesanan.objects.all()
    permission_classes = [IsAuthenticated]
    
    # --- FITUR SEARCH & FILTER ---
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'type_pesanan', 'is_corporate']
    search_fields = ['kode_booking', 'pelanggan__nama', 'perusahaan_nama', 'mobil__nama_mobil']
    ordering_fields = ['created_at', 'tanggal_mulai', 'harga_total']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            if self.request.user.is_staff:
                return AdminCreatePesananSerializer
            return CreatePesananSerializer
        return PesananSerializer
    
    def get_queryset(self):
        user = self.request.user
        base_qs = Pesanan.objects.select_related('pelanggan', 'mobil', 'supir', 'promo')
        if user.is_staff or getattr(user, 'role', '') == 'admin':
            return base_qs.all()
        if hasattr(user, 'pelanggan'):
            return base_qs.filter(pelanggan=user.pelanggan)
        return base_qs.none()

    # --- 1. LOGIKA SAAT MEMBUAT PESANAN (CREATE) ---
    def perform_create(self, serializer):
        instance = serializer.save()
        
        # A. Email ke Admin (Notifikasi Order Baru)
        if instance.type_pesanan == 'online':
            try:
                subject_admin = f"🔔 Pesanan Baru: {instance.kode_booking}"
                msg_admin = f"""
                Halo Admin,
                Ada pesanan baru masuk!
                
                Kode: {instance.kode_booking}
                Mobil: {instance.mobil.nama_mobil}
                Customer: {instance.pelanggan.nama if instance.pelanggan else 'Corporate'}
                Total: Rp {instance.harga_total:,.0f}
                
                Cek dashboard sekarang.
                """
                send_mail(subject_admin, msg_admin, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], fail_silently=True)
            except Exception as e:
                print(f"Gagal email admin: {e}")

        # B. Email ke Customer (Konfirmasi Menunggu)
        if instance.pelanggan and instance.pelanggan.user.email:
            try:
                subject_cust = f"⏳ Menunggu Konfirmasi: {instance.kode_booking}"
                msg_cust = f"""
                Halo {instance.pelanggan.nama},

                Pesanan sewa mobil Anda telah kami terima.
                Status saat ini: MENUNGGU KONFIRMASI ADMIN.

                Detail:
                Mobil: {instance.mobil.nama_mobil}
                Tanggal: {instance.tanggal_mulai} s/d {instance.tanggal_selesai}
                Total: Rp {instance.harga_total:,.0f}

                Kami akan segera menghubungi Anda setelah mengecek ketersediaan unit.
                """
                send_mail(subject_cust, msg_cust, settings.EMAIL_HOST_USER, [instance.pelanggan.user.email], fail_silently=True)
            except Exception as e:
                print(f"Gagal email customer: {e}")

    # --- 2. LOGIKA SAAT UPDATE (Via Form Edit) ---
    def perform_update(self, serializer):
        instance_awal = self.get_object()
        status_lama = instance_awal.status
        
        instance_baru = serializer.save()
        status_baru = instance_baru.status
        
        # Jika status berubah via Edit Form, kirim notif juga
        if status_lama != status_baru:
            self._kirim_email_status(instance_baru)

    # --- HELPER: KIRIM EMAIL STATUS ---
    def _kirim_email_status(self, pesanan):
        if not pesanan.pelanggan or not pesanan.pelanggan.user.email:
            return

        email_to = pesanan.pelanggan.user.email
        subject = ""
        message = ""
        
        if pesanan.status == 'konfirmasi':
            subject = f"✅ Booking Disetujui: {pesanan.kode_booking}"
            message = f"Halo {pesanan.pelanggan.nama}, Booking Anda DISETUJUI! Silakan ambil unit {pesanan.mobil.nama_mobil} sesuai jadwal."
        
        elif pesanan.status == 'batal':
            subject = f"❌ Booking Dibatalkan: {pesanan.kode_booking}"
            message = f"Halo {pesanan.pelanggan.nama}, Mohon maaf booking Anda dibatalkan. Hubungi admin untuk info lebih lanjut."
        
        elif pesanan.status == 'selesai':
            subject = f"👋 Pesanan Selesai: {pesanan.kode_booking}"
            message = f"Terima kasih telah menggunakan jasa kami. Pesanan selesai."
            if pesanan.denda > 0:
                message += f"\n\nCatatan: Terdapat denda keterlambatan sebesar Rp {pesanan.denda:,.0f}."

        if subject:
            try:
                send_mail(subject, message, settings.EMAIL_HOST_USER, [email_to], fail_silently=True)
            except: pass

    # --- 3. CEK KETERSEDIAAN (Anti Zombie & Admin Lupa) ---
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def cek_ketersediaan(self, request):
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        
        if not start or not end:
            return Response({"error": "Parameter tanggal wajib"}, status=400)
            
        today = timezone.now().date()
        
        booked_ids = Pesanan.objects.filter(
            tanggal_mulai__lte=end,
            tanggal_selesai__gte=start
        ).filter(
            # Logic: Hanya anggap sibuk jika masa sewa MASIH BERLAKU (Hari ini atau masa depan)
            # Pesanan masa lalu (walaupun status masih 'aktif'/'pending') dianggap available
            (Q(status__in=['pending', 'konfirmasi']) & Q(tanggal_mulai__gte=today)) |
            (Q(status__in=['lunas', 'sedang_disewa', 'aktif']) & Q(tanggal_selesai__gte=today))
        ).values_list('mobil_id', flat=True)
        
        available_cars = Mobil.objects.filter(status='aktif').exclude(id__in=booked_ids)
        serializer = MobilSerializer(available_cars, many=True, context={'request': request})
        return Response(serializer.data)

    # --- 4. ADMIN ACTIONS (TOMBOL CEPAT) ---
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def konfirmasi(self, request, pk=None):
        pesanan = self.get_object()
        if pesanan.status in ['selesai', 'batal']:
             return Response({'error': 'Pesanan sudah selesai/batal'}, status=400)
        
        pesanan.status = 'konfirmasi'
        pesanan.save()
        
        # Kirim Email
        self._kirim_email_status(pesanan)
        return Response({'status': 'Pesanan dikonfirmasi'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def aktifkan(self, request, pk=None):
        pesanan = self.get_object()
        if pesanan.status != 'konfirmasi':
             return Response({'error': 'Pesanan belum dikonfirmasi'}, status=400)
             
        pesanan.status = 'aktif'
        pesanan.save()
        return Response({'status': 'Pesanan aktif (sedang berjalan)'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def selesai(self, request, pk=None):
        """
        Selesai + Hitung Denda Otomatis
        """
        pesanan = self.get_object()
        
        # 1. Cek Keterlambatan
        today = timezone.now().date()
        tanggal_janji = pesanan.tanggal_selesai
        denda = 0
        info_denda = ""

        if today > tanggal_janji:
            selisih_hari = (today - tanggal_janji).days
            # Rumus: Denda = Harga Sewa * Hari Telat (Bisa disesuaikan)
            denda = selisih_hari * pesanan.mobil.harga_per_hari
            
            pesanan.denda = denda
            info_denda = f"Terlambat {selisih_hari} hari. Denda: Rp {denda:,.0f}"
            
            # Tambahkan ke catatan jika belum ada
            if not pesanan.catatan: pesanan.catatan = ""
            pesanan.catatan += f" | {info_denda}"

        pesanan.status = 'selesai'
        pesanan.save()
        
        # 2. Kirim Email ke Customer
        self._kirim_email_status(pesanan)
        
        return Response({
            'status': 'Pesanan selesai',
            'denda': denda,
            'message': info_denda if denda > 0 else "Tepat waktu"
        })
        
    @action(detail=True, methods=['post'])
    def batal(self, request, pk=None):
        pesanan = self.get_object()
        
        # Customer hanya boleh batal jika masih pending
        if not request.user.is_staff and pesanan.status != 'pending':
            return Response({'error': 'Pesanan yang sudah diproses tidak bisa dibatalkan user.'}, status=400)
            
        pesanan.status = 'batal'
        pesanan.save()
        
        # Kirim Email
        self._kirim_email_status(pesanan)
        return Response({'status': 'Pesanan dibatalkan'})