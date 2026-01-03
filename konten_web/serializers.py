from rest_framework import serializers
from .models import HeroSection, Dokumentasi

class HeroSectionSerializer(serializers.ModelSerializer):
    media_url = serializers.SerializerMethodField()
    media_type = serializers.SerializerMethodField()

    class Meta:
        model = HeroSection
        fields = ['id', 'judul', 'sub_judul', 'background_media', 'media_url', 'media_type', 'is_active', 'urutan']

    def get_media_url(self, obj):
        # PERBAIKAN: Langsung ambil URL dari CloudinaryField
        # Cloudinary otomatis memberikan URL HTTPS lengkap, jadi tidak perlu build_absolute_uri
        if obj.background_media:
            return obj.background_media.url
        return None

    def get_media_type(self, obj):
        """Mendeteksi apakah file itu video atau image"""
        if obj.background_media:
            try:
                # Ambil nama file dari properti .name
                filename = getattr(obj.background_media, 'name', '')
                if not filename:
                    return 'unknown'
                
                ext = filename.split('.')[-1].lower()
                # Tambahkan format video umum
                if ext in ['mp4', 'webm', 'mov', 'mkv', 'avi']:
                    return 'video'
                return 'image'
            except:
                return 'unknown'
        return 'unknown'

class DokumentasiSerializer(serializers.ModelSerializer):
    media_url = serializers.SerializerMethodField()
    media_type = serializers.SerializerMethodField()

    class Meta:
        model = Dokumentasi
        fields = ['id', 'judul', 'deskripsi', 'file_media', 'media_url', 'media_type', 'urutan', 'created_at']

    def get_media_url(self, obj):
        # PERBAIKAN: Langsung return URL Cloudinary
        if obj.file_media:
            return obj.file_media.url
        return None

    def get_media_type(self, obj):
        if obj.file_media:
            try:
                filename = getattr(obj.file_media, 'name', '')
                if not filename:
                    return 'unknown'

                ext = filename.split('.')[-1].lower()
                if ext in ['mp4', 'webm', 'mov', 'mkv', 'avi']:
                    return 'video'
                return 'image'
            except:
                return 'unknown'
        return 'unknown'