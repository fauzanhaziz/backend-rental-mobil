from django.contrib import admin
from .models import Mobil

@admin.register(Mobil)
class MobilAdmin(admin.ModelAdmin):
    list_display = ('nama_mobil', 'merk', 'plat_nomor', 'harga_per_hari', 'status', 'popularity') # Tambah popularity
    list_filter = ('status', 'transmisi', 'popularity') # Tambah filter popularity
    search_fields = ('nama_mobil', 'plat_nomor')
    list_editable = ('status', 'harga_per_hari', 'popularity') # Agar bisa diedit langsung di list