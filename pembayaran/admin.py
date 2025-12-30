from django.contrib import admin
from .models import Pembayaran

@admin.register(Pembayaran)
class PembayaranAdmin(admin.ModelAdmin):
    list_display = ('pesanan', 'metode', 'jumlah', 'status', 'dicatat_oleh', 'created_at')
    list_filter = ('status', 'metode', 'created_at')
    search_fields = ('pesanan__kode_booking',)
    readonly_fields = ('created_at',)