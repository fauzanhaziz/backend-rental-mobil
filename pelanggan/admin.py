from django.contrib import admin
from django.utils.html import format_html
from .models import Pelanggan

@admin.register(Pelanggan)
class PelangganAdmin(admin.ModelAdmin):
    # Menambahkan 'foto_ktp_preview' ke dalam tabel
    list_display = ('nama', 'no_hp', 'ktp', 'foto_ktp_preview', 'get_status_akun', 'created_at')
    
    search_fields = ('nama', 'ktp', 'no_hp')
    list_filter = ('created_at', 'user') # Menambahkan filter berdasarkan user (online/offline)
    
    # Menampilkan detail field saat edit, termasuk preview gambar
    readonly_fields = ('foto_ktp_preview', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Identitas', {
            'fields': ('user', 'nama', 'no_hp', 'alamat')
        }),
        ('Dokumen', {
            'fields': ('ktp', 'foto_ktp', 'foto_ktp_preview', 'foto_sim')
        }),
        ('Lainnya', {
            'fields': ('catatan', 'created_at', 'updated_at')
        }),
    )

    def get_status_akun(self, obj):
        if obj.user:
            return "Online (App)"
        return "Offline (Walk-in)"
    get_status_akun.short_description = 'Tipe'
    
    # --- FITUR PREVIEW GAMBAR ---
    def foto_ktp_preview(self, obj):
        if obj.foto_ktp:
            # Menampilkan gambar kecil (thumbnail)
            return format_html('<img src="{}" style="width: 100px; height: auto; border-radius: 5px;" />', obj.foto_ktp.url)
        return "Belum Upload"
    
    foto_ktp_preview.short_description = "Preview KTP"