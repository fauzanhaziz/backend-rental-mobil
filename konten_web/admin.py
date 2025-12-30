from django.contrib import admin
from .models import HeroSection, Dokumentasi

@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ['judul', 'media_type_preview', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['judul']
    readonly_fields = ['created_at']

    def media_type_preview(self, obj):
        if obj.background_media:
            ext = obj.background_media.name.split('.')[-1].lower()
            return 'VIDEO' if ext in ['mp4', 'webm', 'mov'] else 'GAMBAR'
        return '-'
    media_type_preview.short_description = "Tipe Media"

@admin.register(Dokumentasi)
class DokumentasiAdmin(admin.ModelAdmin):
    list_display = ['judul', 'urutan', 'created_at']
    list_editable = ['urutan']
    search_fields = ['judul']