from django.contrib import admin
from .models import Supir

@admin.register(Supir)
class SupirAdmin(admin.ModelAdmin):
    list_display = ('nama', 'no_hp', 'status', 'harga_per_hari')
    list_filter = ('status',)
    search_fields = ('nama', 'no_hp')
    list_editable = ('status',) # Admin bisa ubah status supir dengan cepat dari tabel