from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PembayaranViewSet

router = DefaultRouter()

# 1. Register ViewSet
# r'pembayaran' -> Menjadikan endpoint: /api/pembayaran/
# basename='pembayaran' -> Wajib ada karena kita custom get_queryset di views.py
router.register(r'pembayaran', PembayaranViewSet, basename='pembayaran')

urlpatterns = [
    path('', include(router.urls)),
]