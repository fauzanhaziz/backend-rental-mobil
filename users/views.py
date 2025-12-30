import os
import random  # <--- Penting untuk generate OTP
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView  # <--- Penting untuk Class Based View baru
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from django.core.mail import send_mail  # <--- Penting untuk kirim email

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from pelanggan.models import Pelanggan
from .models import PasswordResetOTP  # <--- Import Model OTP Baru
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    MyTokenObtainPairSerializer, 
    LoginSerializer, 
    SetPasswordSerializer
)

User = get_user_model()

# --- HELPER: GENERATE SMART TOKEN ---
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    # Custom Claims
    refresh['username'] = user.username
    refresh['role'] = user.role
    refresh['email'] = user.email
    
    if hasattr(user, 'pelanggan'):
        refresh['id_pelanggan'] = user.pelanggan.id
        refresh['nama_pelanggan'] = user.pelanggan.nama
    
    if user.is_staff or user.role == 'admin':
        refresh['is_admin'] = True

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# --- 1. Custom Login View (JWT Biasa) ---
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# --- 2. LOGIN MANUAL ---
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user:
            if not user.is_active:
                return Response({'error': 'Akun tidak aktif.'}, status=status.HTTP_401_UNAUTHORIZED)

            tokens = get_tokens_for_user(user)
            
            return Response({
                'message': 'Login berhasil!',
                'user': UserSerializer(user).data,
                'tokens': tokens 
            })
        
        return Response({'error': 'Username atau password salah!'}, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- 3. Register View ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Registrasi berhasil! Silakan login.',
            'user': UserSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- 4. Logout View ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logout berhasil!'})
    except Exception as e:
        return Response({'error': 'Token tidak valid'}, status=status.HTTP_400_BAD_REQUEST)

# --- 5. GOOGLE LOGIN ---
@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Token Google wajib dikirim'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
        
        if not GOOGLE_CLIENT_ID:
             return Response({'error': 'Server misconfiguration: GOOGLE_CLIENT_ID not set'}, status=500)

        id_info = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )

        email = id_info['email']
        nama = id_info.get('name', '')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            with transaction.atomic():
                username = email.split('@')[0]
                if User.objects.filter(username=username).exists():
                    username += str(random.randint(1000, 9999))

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None,
                    role='customer'
                )
                user.set_unusable_password()
                user.save()

                Pelanggan.objects.create(
                    user=user,
                    nama=nama,
                    no_hp="-",
                    ktp=f"GOOGLE_{username}"
                )

        if not user.is_active:
             return Response({'error': 'Akun dinonaktifkan.'}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Login Google berhasil!',
            'user': UserSerializer(user).data,
            'tokens': tokens
        })

    except ValueError:
        return Response({'error': 'Token Google tidak valid'}, status=status.HTTP_400_BAD_REQUEST)

# --- 6. USER MANAGEMENT & SET PASSWORD ---
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'customer':
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def set_password(self, request):
        user = request.user
        serializer = SetPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            current_password = serializer.validated_data.get('current_password')

            if user.has_usable_password():
                if not current_password:
                    return Response({'error': 'Password lama wajib diisi.'}, status=status.HTTP_400_BAD_REQUEST)
                if not user.check_password(current_password):
                    return Response({'error': 'Password lama salah.'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password berhasil diperbarui.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- 7. PASSWORD RESET (OTP SYSTEM - NEW) ---

class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email wajib diisi.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            
            # 1. Generate Kode 6 Digit
            otp = str(random.randint(100000, 999999))
            
            # 2. Simpan ke Database
            PasswordResetOTP.objects.update_or_create(
                user=user,
                defaults={'otp_code': otp}
            )

            # 3. Kirim Email
            send_mail(
                subject="Kode Reset Password - Rental Mobil",
                message=f"Kode OTP Anda adalah: {otp}\n\nJangan berikan kode ini ke siapapun.",
                from_email="noreply@rentalmobil.com",
                recipient_list=[email],
                fail_silently=False,
            )

            return Response({'message': 'Kode OTP terkirim ke email.'})

        except User.DoesNotExist:
            # Tetap return sukses agar tidak bocor info email valid/tidak
            return Response({'message': 'Kode OTP terkirim ke email.'})

class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not email or not otp or not new_password:
            return Response({'error': 'Data tidak lengkap.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'error': 'Password tidak cocok.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Cek User
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
             return Response({'error': 'Email tidak valid.'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Cek OTP
        try:
            otp_record = PasswordResetOTP.objects.get(user=user)
            if otp_record.otp_code != otp:
                return Response({'error': 'Kode OTP salah.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 3. Ganti Password
            user.set_password(new_password)
            user.save()

            # 4. Hapus OTP
            otp_record.delete()

            return Response({'message': 'Password berhasil diubah. Silakan login.'})

        except PasswordResetOTP.DoesNotExist:
            return Response({'error': 'Kode OTP tidak ditemukan atau sudah kadaluarsa.'}, status=status.HTTP_400_BAD_REQUEST)