from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupirViewSet

router = DefaultRouter()
router.register(r'', SupirViewSet) # Endpoint: /api/supir/

urlpatterns = [
    path('', include(router.urls)),
]