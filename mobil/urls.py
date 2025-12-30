from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MobilViewSet

router = DefaultRouter()
router.register(r'', MobilViewSet) # Endpoint: /api/mobil/

urlpatterns = [
    path('', include(router.urls)),
]