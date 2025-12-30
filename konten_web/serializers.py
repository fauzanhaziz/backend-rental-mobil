from rest_framework import serializers
from .models import HeroSection, Dokumentasi

class HeroSectionSerializer(serializers.ModelSerializer):
    media_url = serializers.SerializerMethodField()
    media_type = serializers.SerializerMethodField()

    class Meta:
        model = HeroSection
        fields = ['id', 'judul', 'sub_judul', 'background_media', 'media_url', 'media_type', 'is_active', 'urutan']

    def get_media_url(self, obj):
        request = self.context.get('request')
        # Tambahkan cek 'if request' agar tidak error jika dijalankan di shell/testing
        if request and obj.background_media:
            return request.build_absolute_uri(obj.background_media.url)
        return None

    def get_media_type(self, obj):
        """Mendeteksi apakah file itu video atau image"""
        if obj.background_media:
            # Ambil ekstensi dan lower case
            try:
                ext = obj.background_media.name.split('.')[-1].lower()
                if ext in ['mp4', 'webm', 'mov', 'mkv']:
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
        request = self.context.get('request')
        # Tambahkan cek 'if request'
        if request and obj.file_media:
            return request.build_absolute_uri(obj.file_media.url)
        return None

    def get_media_type(self, obj):
        if obj.file_media:
            try:
                ext = obj.file_media.name.split('.')[-1].lower()
                if ext in ['mp4', 'webm', 'mov', 'mkv']:
                    return 'video'
                return 'image'
            except:
                return 'unknown'
        return 'unknown'