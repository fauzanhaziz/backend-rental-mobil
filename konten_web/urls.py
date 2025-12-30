from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebsiteContentViewSet, AdminHeroViewSet, AdminDokumentasiViewSet

router = DefaultRouter()

# Endpoint Publik (Read Only)
router.register(r'public', WebsiteContentViewSet, basename='konten-public')

# Endpoint Admin (CRUD)
router.register(r'hero', AdminHeroViewSet, basename='admin-hero')
router.register(r'dokumentasi', AdminDokumentasiViewSet, basename='admin-docs')

urlpatterns = [
    path('', include(router.urls)),
]