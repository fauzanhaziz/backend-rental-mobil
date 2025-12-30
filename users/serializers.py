from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from pelanggan.models import Pelanggan

User = get_user_model()

# --- 1. USER SERIALIZER (Output Data User) ---
class UserSerializer(serializers.ModelSerializer):
    # Field tambahan untuk memberi tahu frontend apakah user punya password (untuk user Google)
    has_password = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_active', 'date_joined', 'has_password']
        read_only_fields = ['id', 'date_joined', 'role', 'has_password']

    def get_has_password(self, obj):
        return obj.has_usable_password()

# --- 2. REGISTER SERIALIZER ---
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer Register: Membuat User + Profil Pelanggan (Tanpa KTP dulu)
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    # Data Profil Pelanggan (Cukup Nama & HP saat register awal)
    nama = serializers.CharField(write_only=True)
    no_hp = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'nama', 'no_hp']
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Password tidak sama!")
        return data
    
    def create(self, validated_data):
        nama = validated_data.pop('nama')
        no_hp = validated_data.pop('no_hp')
        validated_data.pop('password2')
        
        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                role='customer'
            )
            
            # Buat pelanggan TANPA KTP (ktp=None) dan TANPA FOTO dulu
            Pelanggan.objects.create(
                user=user,
                nama=nama,
                no_hp=no_hp,
                ktp=None 
            )
            
        return user

# --- 3. LOGIN SERIALIZER ---
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

# --- 4. JWT TOKEN SERIALIZER (Custom Claims) ---
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Token: Menyisipkan Role & ID Pelanggan ke dalam Token.
    Agar Frontend tidak perlu request API lagi untuk tau siapa yang login.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Custom Claims
        token['username'] = user.username
        token['role'] = user.role
        token['email'] = user.email
        
        # Jika user adalah customer, masukkan ID & Nama Pelanggan
        if hasattr(user, 'pelanggan'):
            token['id_pelanggan'] = user.pelanggan.id
            token['nama_pelanggan'] = user.pelanggan.nama
        
        # Jika admin, tandai
        if user.is_staff or user.role == 'admin':
            token['is_admin'] = True

        return token
    
# --- 5. SET PASSWORD SERIALIZER (GANTI PASSWORD SAAT LOGIN) ---
class SetPasswordSerializer(serializers.Serializer):
    """
    Untuk Ganti Password atau Set Password (User Google) di Halaman Profil (Saat Login)
    """
    current_password = serializers.CharField(required=False) # Tidak wajib jika user Google
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password konfirmasi tidak sama."})
        return data

# --- 6. RESET PASSWORD SERIALIZERS (OTP SYSTEM) ---
# Ini serializer baru untuk mendukung fitur Lupa Password OTP

class PasswordResetOTPRequestSerializer(serializers.Serializer):
    """
    Validasi input untuk Request OTP (Hanya butuh email)
    """
    email = serializers.EmailField()

class PasswordResetOTPConfirmSerializer(serializers.Serializer):
    """
    Validasi input untuk Konfirmasi OTP & Ganti Password Baru
    """
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password konfirmasi tidak cocok."})
        return data