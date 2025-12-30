from rest_framework import serializers
from django.db.models import Q
from .models import Pesanan
from pelanggan.models import Pelanggan
from pelanggan.serializers import PelangganSerializer
from mobil.serializers import MobilSerializer
from supir.serializers import SupirSerializer
from promo.serializers import PromoSerializer

# --- 1. SERIALIZER READ (Menampilkan Data) ---
class PesananSerializer(serializers.ModelSerializer):
    pelanggan_detail = PelangganSerializer(source='pelanggan', read_only=True)
    mobil_detail = MobilSerializer(source='mobil', read_only=True)
    supir_detail = SupirSerializer(source='supir', read_only=True)
    promo_detail = PromoSerializer(source='promo', read_only=True)
    
    link_wa = serializers.CharField(source='link_wa_konfirmasi', read_only=True)
    
    class Meta:
        model = Pesanan
        fields = [
            'id', 'kode_booking', 'pelanggan_detail', 'mobil_detail', 
            'supir_detail', 'promo_detail', 'tanggal_mulai', 'tanggal_selesai', 
            'total_hari', 'harga_total', 'denda', 'status', 'type_pesanan', 
            'catatan', 'link_wa', 'created_at', 'bukti_ktp',
            
            # Field Corporate
            'is_corporate', 'perusahaan_nama', 'perusahaan_npwp', 
            'perusahaan_alamat', 'perusahaan_pic', 'perusahaan_pic_kontak'
        ]

# --- 2. SERIALIZER CREATE BASE (Logic Utama) ---
class BaseCreatePesananSerializer(serializers.ModelSerializer):
    tanggal_mulai = serializers.DateField()
    tanggal_selesai = serializers.DateField()
    
    class Meta:
        model = Pesanan
        fields = [
            'mobil', 'supir', 'promo', 'tanggal_mulai', 'tanggal_selesai', 'catatan', 'bukti_ktp',
            'is_corporate', 'perusahaan_nama', 'perusahaan_npwp', 
            'perusahaan_alamat', 'perusahaan_pic', 'perusahaan_pic_kontak'
        ]

    def validate(self, data):
        start = data.get('tanggal_mulai')
        end = data.get('tanggal_selesai')
        mobil = data.get('mobil')
        supir = data.get('supir')

        # 1. Validasi Tanggal Dasar
        if start and end and start > end:
            raise serializers.ValidationError({"tanggal_selesai": "Tanggal selesai tidak boleh sebelum tanggal mulai."})

        # --- LOGIKA CEK BENTROK MOBIL ---
        # Kita cari pesanan lain yang:
        # A. Mobilnya sama
        # B. Statusnya Masih Aktif (Bukan Batal/Selesai)
        # C. Tanggalnya tumpang tindih (Overlap)
        
        # Daftar status yang dianggap "Booking Aktif"
        status_aktif = ['pending', 'konfirmasi', 'lunas', 'sedang_disewa', 'aktif']

        if mobil and start and end:
            bentrok_mobil = Pesanan.objects.filter(
                mobil=mobil,
                status__in=status_aktif
            ).filter(
                # Rumus Overlap: (StartA <= EndB) AND (EndA >= StartB)
                Q(tanggal_mulai__lte=end) & Q(tanggal_selesai__gte=start)
            )

            # PENTING: Jika sedang Edit (Update), jangan cek diri sendiri
            if self.instance:
                bentrok_mobil = bentrok_mobil.exclude(id=self.instance.id)

            if bentrok_mobil.exists():
                detail = bentrok_mobil.first()
                msg = f"Mobil {mobil.nama_mobil} tidak tersedia. Sudah dibooking tanggal {detail.tanggal_mulai} s/d {detail.tanggal_selesai}."
                raise serializers.ValidationError({"mobil": msg})

        # --- LOGIKA CEK BENTROK SUPIR (Jika Ada) ---
        if supir and start and end:
            bentrok_supir = Pesanan.objects.filter(
                supir=supir,
                status__in=status_aktif
            ).filter(
                Q(tanggal_mulai__lte=end) & Q(tanggal_selesai__gte=start)
            )

            if self.instance:
                bentrok_supir = bentrok_supir.exclude(id=self.instance.id)

            if bentrok_supir.exists():
                raise serializers.ValidationError({"supir": f"Supir {supir.nama} sedang bertugas di tanggal tersebut."})

        # Validasi Data Corporate
        if data.get('is_corporate'):
            if not data.get('perusahaan_nama'):
                raise serializers.ValidationError({"perusahaan_nama": "Nama perusahaan wajib diisi untuk sewa corporate."})

        return data

    def calculate_price(self, validated_data):
        mobil = validated_data['mobil']
        supir = validated_data.get('supir')
        promo = validated_data.get('promo')
        start = validated_data['tanggal_mulai']
        end = validated_data['tanggal_selesai']
        
        durasi = (end - start).days + 1
        total = mobil.harga_per_hari * durasi
        
        if supir:
            total += (supir.harga_per_hari * durasi)
            
        if promo:
             # Cek validitas promo method aman
             if hasattr(promo, 'is_valid_now') and promo.is_valid_now:
                total -= promo.nominal_potongan
             elif hasattr(promo, 'is_valid') and promo.is_valid:
                total -= promo.nominal_potongan
            
        return max(total, 0)

# --- 3. CREATE ONLINE ---
class CreatePesananSerializer(BaseCreatePesananSerializer):
    class Meta(BaseCreatePesananSerializer.Meta):
        fields = BaseCreatePesananSerializer.Meta.fields + ['kode_booking', 'harga_total']
        read_only_fields = ['kode_booking', 'harga_total']

    def create(self, validated_data):
        user = self.context['request'].user
        
        if not hasattr(user, 'pelanggan'):
            raise serializers.ValidationError("Anda belum melengkapi profil pelanggan.")
            
        harga = self.calculate_price(validated_data)
        
        return Pesanan.objects.create(
            pelanggan=user.pelanggan,
            harga_total=harga,
            type_pesanan='online',
            status='pending', # Default online
            **validated_data
        )

# --- 4. CREATE OFFLINE ---
class AdminCreatePesananSerializer(BaseCreatePesananSerializer):
    pelanggan_id = serializers.PrimaryKeyRelatedField(
        queryset=Pelanggan.objects.all(), source='pelanggan', write_only=True
    )
    
    class Meta(BaseCreatePesananSerializer.Meta):
        fields = BaseCreatePesananSerializer.Meta.fields + ['pelanggan_id', 'kode_booking', 'harga_total']
        read_only_fields = ['kode_booking', 'harga_total']
        
    def create(self, validated_data):
        harga = self.calculate_price(validated_data)
        
        return Pesanan.objects.create(
            harga_total=harga,
            type_pesanan='offline',
            status='konfirmasi', # Default offline langsung konfirmasi
            **validated_data
        )