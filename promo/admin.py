from django.contrib import admin
from .models import Promo

@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    # Sesuaikan list_display dengan field baru
    list_display = (
        'kode', 
        'nama_promo', 
        'tipe_diskon', 
        'nilai_diskon', # <-- Ganti 'nominal_potongan' jadi ini
        'kuota',
        'berlaku_sampai', 
        'aktif'
    )
    
    list_filter = ('tipe_diskon', 'aktif', 'berlaku_mulai', 'berlaku_sampai')
    search_fields = ('kode', 'nama_promo')
    ordering = ('-berlaku_sampai',)
    
    # Supaya form input lebih rapi dikelompokkan (Optional)
    fieldsets = (
        ('Identitas Promo', {
            'fields': ('kode', 'nama_promo', 'keterangan', 'aktif')
        }),
        ('Aturan Diskon', {
            'fields': ('tipe_diskon', 'nilai_diskon', 'max_potongan', 'min_transaksi')
        }),
        ('Validasi', {
            'fields': ('kuota', 'berlaku_mulai', 'berlaku_sampai')
        }),
    )