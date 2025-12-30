from django.contrib import admin
from .models import Pesanan

@admin.register(Pesanan)
class PesananAdmin(admin.ModelAdmin):
    list_display = ('kode_booking', 'pelanggan', 'mobil', 'tanggal_mulai', 'status', 'type_pesanan', 'harga_total')
    list_filter = ('status', 'type_pesanan', 'created_at')
    search_fields = ('kode_booking', 'pelanggan__nama')
    readonly_fields = ('kode_booking', 'total_hari', 'harga_total', 'created_at')