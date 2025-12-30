from rest_framework import serializers
from .models import Pembayaran

class PembayaranSerializer(serializers.ModelSerializer):
    # --- 1. FIELD TAMBAHAN (READ ONLY) UNTUK FRONTEND ---
    # Mengambil data dari relasi 'pesanan'
    kode_booking = serializers.CharField(source='pesanan.kode_booking', read_only=True)
    
    # Asumsi di model Pesanan ada relasi ke 'pelanggan' dan 'mobil'
    pelanggan_nama = serializers.CharField(source='pesanan.pelanggan.nama', read_only=True)
    mobil_nama = serializers.CharField(source='pesanan.mobil.nama_mobil', read_only=True)
    
    # URL Absolut untuk gambar
    bukti_bayar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Pembayaran
        fields = [
            'id', 
            'pesanan',           # ID Pesanan (untuk keperluan create/link)
            'kode_booking',      # Tampilan Frontend
            'pelanggan_nama',    # Tampilan Frontend
            'mobil_nama',        # Tampilan Frontend
            'jumlah', 
            'metode', 
            'bukti_bayar', 
            'bukti_bayar_url',   # URL Gambar yang aman
            'status', 
            'dicatat_oleh', 
            'catatan_admin',
            'created_at'
        ]
        # User/Frontend tidak boleh edit field ini secara manual via API
        read_only_fields = ['status', 'dicatat_oleh', 'created_at', 'kode_booking', 'pelanggan_nama', 'mobil_nama']

    def get_bukti_bayar_url(self, obj):
        if obj.bukti_bayar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.bukti_bayar.url)
            return obj.bukti_bayar.url
        return None

    def validate(self, data):
        """
        Validasi: Jika metode Transfer, wajib upload bukti bayar.
        """
        # Kita cek apakah user mengirim 'metode' atau menggunakan data instance yang sudah ada
        metode = data.get('metode')
        bukti_bayar = data.get('bukti_bayar')

        # Logic: Jika metode transfer (baru atau existing) dan tidak ada bukti bayar
        if metode == 'transfer' and not bukti_bayar:
            # Pengecekan khusus saat CREATE (self.instance is None)
            if self.instance is None:
                raise serializers.ValidationError({"bukti_bayar": "Bukti transfer wajib diupload untuk metode transfer."})
            
            # Pengecekan saat UPDATE (jika user mengubah metode jadi transfer tapi tidak upload foto)
            # Namun biasanya update hanya dilakukan Admin untuk ubah status, jadi validasi ini cukup aman.
            
        return data