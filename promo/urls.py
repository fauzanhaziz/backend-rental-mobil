from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PromoViewSet

router = DefaultRouter()
router.register(r'', PromoViewSet, basename='promo')

urlpatterns = [
    path('', include(router.urls)),
]