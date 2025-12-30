from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import HeroSection, Dokumentasi
from .serializers import HeroSectionSerializer, DokumentasiSerializer

# --- ADMIN VIEWSETS (CRUD) ---

class AdminHeroViewSet(viewsets.ModelViewSet):
    """Admin bisa tambah/edit/hapus konfigurasi Hero"""
    queryset = HeroSection.objects.all().order_by('urutan', '-created_at')
    serializer_class = HeroSectionSerializer
    permission_classes = [IsAdminUser] 
    
    # 2. TAMBAHKAN 'JSONParser' KE DALAM LIST INI
    parser_classes = [MultiPartParser, FormParser, JSONParser]

class AdminDokumentasiViewSet(viewsets.ModelViewSet):
    """Admin bisa kelola dokumentasi"""
    queryset = Dokumentasi.objects.all().order_by('urutan', '-created_at')
    serializer_class = DokumentasiSerializer
    permission_classes = [IsAdminUser]
    
    # 3. TAMBAHKAN JUGA DI SINI (Supaya aman kedepannya)
    parser_classes = [MultiPartParser, FormParser, JSONParser]

# --- PUBLIC VIEWSET (READ ONLY) ---

class WebsiteContentViewSet(viewsets.ViewSet):
    """
    Satu ViewSet untuk menangani semua konten publik website
    """
    permission_classes = [AllowAny] 

    @action(detail=False, methods=['get'])
    def hero(self, request):
        """
        Ambil SEMUA Hero Section yang aktif, diurutkan berdasarkan 'urutan'
        """
        heroes = HeroSection.objects.filter(is_active=True).order_by('urutan', '-created_at')
        
        # many=True WAJIB ADA agar return JSON Array []
        serializer = HeroSectionSerializer(heroes, many=True, context={'request': request})
        
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dokumentasi(self, request):
        docs = Dokumentasi.objects.all().order_by('urutan', '-created_at')
        serializer = DokumentasiSerializer(docs, many=True, context={'request': request})
        return Response(serializer.data)