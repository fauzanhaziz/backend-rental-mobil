from django.db import models
from django.core.exceptions import ValidationError
from pelanggan.models import Pelanggan
from mobil.models import Mobil
from supir.models import Supir
from promo.models import Promo
import random
import string
import urllib.parse
from datetime import timedelta

class Pesanan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Menunggu Pembayaran'),
        ('konfirmasi', 'Dikonfirmasi / Siap Ambil'),
        ('aktif', 'Sedang Disewa'),
        ('selesai', 'Selesai / Dikembalikan'),
        ('batal', 'Dibatalkan'),
    ]
    
    TYPE_CHOICES = [
        ('online', 'Online (Web)'),
        ('offline', 'Offline (Walk-in/WA)'),
    ]
    
    # Identitas Unik
    kode_booking = models.CharField(max_length=20, unique=True, editable=False)
    
    # Relasi Utama
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.RESTRICT, related_name='pesanan')
    mobil = models.ForeignKey(Mobil, on_delete=models.RESTRICT, related_name='pesanan')
    supir = models.ForeignKey(Supir, on_delete=models.SET_NULL, null=True, blank=True, related_name='pesanan')
    promo = models.ForeignKey(Promo, on_delete=models.SET_NULL, null=True, blank=True, related_name='pesanan')
    
    # --- DATA WAKTU SEWA ---
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    total_hari = models.IntegerField(editable=False, default=1)
    
    # --- KEUANGAN ---
    # Default 0 agar tidak error saat create awal, nanti dihitung ulang
    harga_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total biaya sewa")
    denda = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # --- META DATA ---
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    type_pesanan = models.CharField(max_length=20, choices=TYPE_CHOICES, default='online')
    catatan = models.TextField(blank=True, null=True)

    bukti_ktp = models.ImageField(upload_to='ktp_uploads/%Y/%m/', blank=True, null=True, help_text="Foto KTP penyewa")

    # --- FITUR BARU: DATA PERUSAHAAN (CORPORATE B2B) ---
    is_corporate = models.BooleanField(default=False, help_text="Centang jika penyewa adalah perusahaan")
    perusahaan_nama = models.CharField(max_length=150, blank=True, null=True)
    perusahaan_npwp = models.CharField(max_length=50, blank=True, null=True)
    perusahaan_alamat = models.TextField(blank=True, null=True)
    perusahaan_pic = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nama PIC")
    perusahaan_pic_kontak = models.CharField(max_length=50, blank=True, null=True, verbose_name="Kontak PIC")
    
    wa_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pesanan'
        ordering = ['-created_at']
        verbose_name = 'Pesanan'
        verbose_name_plural = 'Data Pesanan'
        indexes = [
            models.Index(fields=['tanggal_mulai', 'tanggal_selesai']),
            models.Index(fields=['status']),
            models.Index(fields=['kode_booking']),
        ]
    
    def __str__(self):
        return f"{self.kode_booking} - {self.pelanggan.nama}"
    
    def clean(self):
        """Validasi Anti-Bentrok & Tanggal"""
        if self.tanggal_mulai and self.tanggal_selesai:
            if self.tanggal_mulai > self.tanggal_selesai:
                raise ValidationError("Tanggal selesai harus setelah tanggal mulai.")

            # Cek Tabrakan Jadwal (Exclude diri sendiri saat edit)
            overlap = Pesanan.objects.filter(
                mobil=self.mobil,
                status__in=['pending', 'konfirmasi', 'aktif'], # Status yg memblokir mobil
                tanggal_mulai__lte=self.tanggal_selesai,
                tanggal_selesai__gte=self.tanggal_mulai
            ).exclude(pk=self.pk)

            if overlap.exists():
                raise ValidationError(f"Mobil {self.mobil.nama_mobil} tidak tersedia pada tanggal tersebut.")

    def save(self, *args, **kwargs):
        # 1. Generate Kode Booking (TRX-HURUFANGKA)
        if not self.kode_booking:
            self.kode_booking = 'TRX-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # 2. Hitung Total Hari
        if self.tanggal_mulai and self.tanggal_selesai:
            delta = self.tanggal_selesai - self.tanggal_mulai
            self.total_hari = delta.days + 1 # Hitungan sewa harian (inklusif)
            
        # 3. Hitung Harga Total Otomatis (Basic Calculation)
        # Jika frontend mengirim 0 atau kosong, backend akan menghitung estimasi
        if self.harga_total == 0 and self.mobil:
            harga_mobil = self.mobil.harga_per_hari * self.total_hari
            harga_supir = 0
            if self.supir:
                harga_supir = self.supir.harga_per_hari * self.total_hari
            self.harga_total = harga_mobil + harga_supir

        super().save(*args, **kwargs)

    @property
    def link_wa_konfirmasi(self):
        phone_number = "6281365338011" # Sesuaikan nomor admin
        
        # Bedakan sapaan corporate vs personal
        penyewa = self.perusahaan_nama if self.is_corporate else self.pelanggan.nama
        
        message = (
            f"Halo Admin, konfirmasi pesanan baru:\n\n"
            f"Kode: *{self.kode_booking}*\n"
            f"Penyewa: {penyewa}\n"
            f"Unit: {self.mobil.nama_mobil}\n"
            f"Tgl: {self.tanggal_mulai} s/d {self.tanggal_selesai}\n"
            f"Total: Rp {self.harga_total:,.0f}\n"
        )
        return f"https://wa.me/{phone_number}?text={urllib.parse.quote(message)}"