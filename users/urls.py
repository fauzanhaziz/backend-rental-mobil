from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserViewSet, 
    register, 
    login, 
    logout, 
    google_login,
    RequestPasswordResetView,  # <--- View OTP Baru
    ResetPasswordConfirmView
)

router = DefaultRouter()
router.register(r'', UserViewSet) 

urlpatterns = [
    # --- AUTH ENDPOINTS ---
    path('auth/register/', register, name='auth_register'),
    path('auth/login/', login, name='auth_login'),
    path('auth/google/', google_login, name='auth_google'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', logout, name='auth_logout'),
    
    
    # --- PASSWORD RESET ENDPOINTS ---
    path('password-reset/request/', RequestPasswordResetView.as_view(), name='request-reset'),
    path('password-reset/confirm/', ResetPasswordConfirmView.as_view(), name='confirm-reset'),
    
    # --- USER CRUD ---
    path('', include(router.urls)),
]