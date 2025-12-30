from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from .models import Supir
from .serializers import SupirSerializer

class SupirViewSet(viewsets.ModelViewSet):
    queryset = Supir.objects.all()
    serializer_class = SupirSerializer
    
    # Search & Filter
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nama', 'no_hp']
    ordering_fields = ['nama', 'status']
    
    def get_permissions(self):
        """
        Logika Permission:
        - Create/Update/Delete: HANYA Admin
        - List/Retrieve: Semua User Authenticated boleh (User umum bisa lihat info supir)
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        queryset = Supir.objects.all()
        
        # Filter by Status (berguna untuk Admin saat assign supir)
        # Contoh URL: /api/supir/?status=tersedia
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset