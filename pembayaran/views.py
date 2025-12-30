from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from .models import Pembayaran
from .serializers import PembayaranSerializer

class PembayaranViewSet(viewsets.ModelViewSet):
    queryset = Pembayaran.objects.all()
    serializer_class = PembayaranSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] # Support Upload File (Gambar Bukti)

    # --- KONFIGURASI FILTER & SEARCH ---
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter dropdown (misal: /api/pembayaran/?status=pending)
    filterset_fields = ['status', 'metode']
    
    # Kolom Pencarian (misal: /api/pembayaran/?search=TRX-001)
    # Sesuaikan dengan nama field di model Pesanan & Pelanggan Anda
    search_fields = ['pesanan__kode_booking', 'pesanan__pelanggan__nama']
    
    # Default urutan (Terbaru diatas)
    ordering_fields = ['created_at', 'jumlah']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Logic Queryset:
        - Admin/Staff: Melihat semua data pembayaran.
        - Customer: Hanya melihat pembayaran milik pesanan mereka sendiri.
        """
        user = self.request.user
        
        # Optimasi query: ambil data pesanan, pelanggan, dan mobil dalam 1 query
        base_qs = Pembayaran.objects.select_related(
            'pesanan', 
            'pesanan__pelanggan', 
            'pesanan__mobil'
        )

        # Cek jika Admin
        if user.is_staff or getattr(user, 'role', '') == 'admin':
            return base_qs.all()
        
        # Cek jika Customer (Punya profil pelanggan)
        if hasattr(user, 'pelanggan'):
            return base_qs.filter(pesanan__pelanggan__user=user)
            
        return base_qs.none()

    def perform_create(self, serializer):
        """
        Otomatisasi saat Create Pembayaran (Upload Bukti / Bayar Tunai)
        """
        user = self.request.user
        
        # Skenario 1: Admin Input (Biasanya CASH / OFFLINE di Kantor)
        if user.is_staff or getattr(user, 'role', '') == 'admin':
            serializer.save(
                status='lunas',         # Langsung Lunas karena Admin yang terima
                dicatat_oleh=user       # Catat ID Admin
            )
            # Signal akan otomatis ubah status Pesanan jadi 'konfirmasi'

        # Skenario 2: Customer Input (Upload Bukti Transfer)
        else:
            serializer.save(
                metode='transfer',      # Paksa transfer jika customer input sendiri
                status='pending',       # Wajib pending untuk dicek admin
                dicatat_oleh=None
            )

    def perform_update(self, serializer):
        """
        Logic saat Admin melakukan Update (Verifikasi Lunas/Tolak) via tombol Aksi di Frontend
        """
        user = self.request.user
        
        # Ambil status dari request data (karena di serializer mungkin read_only)
        new_status = self.request.data.get('status')

        # Cek apakah yang melakukan update adalah Admin
        if user.is_staff or getattr(user, 'role', '') == 'admin':
            if new_status:
                # Jika Admin mengubah status, simpan status baru dan catat adminnya
                serializer.save(
                    status=new_status,
                    dicatat_oleh=user
                )
            else:
                # Update biasa tanpa ubah status
                serializer.save()
        else:
            # Jika Customer mencoba update (biasanya dilarang/tidak ada akses tombol)
            # Tapi untuk keamanan, kita cegah perubahan status
            if new_status and new_status != serializer.instance.status:
                raise PermissionDenied("Customer tidak boleh mengubah status pembayaran.")
            
            serializer.save()
            
        # NOTE: Status Pesanan akan berubah otomatis via signals.py yang sudah kita buat