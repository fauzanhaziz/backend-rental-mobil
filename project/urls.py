from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Admin Panel Django
    path('admin/', admin.site.urls),
    
    # 2. Endpoint API untuk Setiap Modul
    # Login, Register, User Profile
    path('api/users/', include('users.urls')),
    
    # Data Pelanggan (Profil Lengkap, KTP, SIM)
    path('api/pelanggan/', include('pelanggan.urls')),
    
    # Master Data Mobil (Katalog, Filter)
    path('api/mobil/', include('mobil.urls')),
    
    # Master Data Supir
    path('api/supir/', include('supir.urls')),
    
    # Data Promo / Diskon
    path('api/promo/', include('promo.urls')),
    
    # Transaksi Pesanan (Booking, Cek Ketersediaan)
    path('api/pesanan/', include('pesanan.urls')),
    
    # Transaksi Pembayaran (Upload Bukti, Verifikasi)
    path('api/pembayaran/', include('pembayaran.urls')),

    path('api/konten/', include('konten_web.urls')),

    #path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
]

# 3. Konfigurasi untuk menampilkan Gambar (Media) di mode Development
# Tanpa ini, gambar mobil dan bukti bayar akan error 404 (Not Found)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 4. Kustomisasi Teks Header Admin Panel (Opsional - Biar terlihat profesional)
admin.site.site_header = "Rental Mobil Dashboard"
admin.site.site_title = "Admin Rental Mobil"
admin.site.index_title = "Selamat Datang di Panel Admin"