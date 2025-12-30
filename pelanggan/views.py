from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
# --- WAJIB IMPORT INI UNTUK UPLOAD FILE ---
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser 

from .models import Pelanggan
from .serializers import PelangganSerializer

class PelangganViewSet(viewsets.ModelViewSet):
    queryset = Pelanggan.objects.all()
    serializer_class = PelangganSerializer
    permission_classes = [IsAuthenticated]
    
    # --- TAMBAHKAN INI AGAR BISA TERIMA FILE GAMBAR ---
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    # Fitur Search untuk Admin (Cari nama/KTP)
    filter_backends = [filters.SearchFilter]
    search_fields = ['nama', 'ktp', 'no_hp']

    def get_queryset(self):
        user = self.request.user
        
        # 1. Jika Admin: Tampilkan SEMUA data pelanggan (Online & Offline)
        if user.is_staff or getattr(user, 'role', '') == 'admin':
            return Pelanggan.objects.all()
        
        # 2. Jika Customer Biasa: HANYA tampilkan profil dia sendiri
        return Pelanggan.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Logika pembuatan Profil Pelanggan
        """
        user = self.request.user

        # Jika Admin yang buat -> Berarti Input Pelanggan OFFLINE (user=None)
        if user.is_staff or getattr(user, 'role', '') == 'admin':
            serializer.save(user=None)
        
        # Jika Customer yang buat -> Berarti Melengkapi Profil Sendiri (user=request.user)
        else:
            # Cek apakah user ini sudah punya profil?
            if Pelanggan.objects.filter(user=user).exists():
                raise PermissionDenied("Anda sudah memiliki profil pelanggan.")
            serializer.save(user=user)