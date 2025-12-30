from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Promo(models.Model):
    # Pilihan Tipe Diskon
    TIPE_DISKON_CHOICES = (
        ('nominal', 'Nominal (Rp)'),
        ('persen', 'Persentase (%)'),
    )

    kode = models.CharField(max_length=20, unique=True, help_text="Kode unik (otomatis uppercase)")
    nama_promo = models.CharField(max_length=100)
    keterangan = models.TextField(blank=True, null=True)
    
    # Logika Diskon
    tipe_diskon = models.CharField(max_length=10, choices=TIPE_DISKON_CHOICES, default='nominal')
    nilai_diskon = models.DecimalField(max_digits=12, decimal_places=2, help_text="Masukkan nominal Rp atau angka Persen")
    max_potongan = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Maksimal potongan (khusus tipe persen). Isi 0 jika tidak ada batas.")
    
    # Syarat
    min_transaksi = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Kuota (Limit)
    kuota = models.PositiveIntegerField(default=0, help_text="Batas jumlah penggunaan promo. Isi 0 jika unlimited.")
    sudah_digunakan = models.PositiveIntegerField(default=0, editable=False, help_text="Jumlah kali promo ini sudah dipakai")

    # Waktu (Ganti ke DateTimeField agar lebih presisi jam-nya)
    berlaku_mulai = models.DateTimeField()
    berlaku_sampai = models.DateTimeField()
    
    aktif = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'promo'
        ordering = ['-berlaku_sampai']
        verbose_name = 'Promo'
        verbose_name_plural = 'Data Promo'

    def __str__(self):
        val = f"Rp {self.nilai_diskon:,.0f}" if self.tipe_diskon == 'nominal' else f"{self.nilai_diskon:.0f}%"
        return f"{self.kode} ({val})"
    
    def save(self, *args, **kwargs):
        # Otomatis ubah kode jadi huruf besar sebelum simpan
        self.kode = self.kode.upper()
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """Cek validitas dasar (Waktu, Aktif, dan Kuota)"""
        now = timezone.now()
        
        # 1. Cek Status Aktif
        if not self.aktif:
            return False
            
        # 2. Cek Tanggal
        if not (self.berlaku_mulai <= now <= self.berlaku_sampai):
            return False
            
        # 3. Cek Kuota (Jika kuota > 0, cek apakah sudah habis)
        if self.kuota > 0 and self.sudah_digunakan >= self.kuota:
            return False
            
        return True

    def hitung_potongan(self, total_belanja):
        """
        Helper function untuk menghitung nilai rupiah diskon berdasarkan total belanja
        """
        # Cek minimum transaksi
        if total_belanja < self.min_transaksi:
            return 0

        potongan = 0
        if self.tipe_diskon == 'nominal':
            potongan = self.nilai_diskon
        elif self.tipe_diskon == 'persen':
            potongan = total_belanja * (self.nilai_diskon / 100)
            # Cek batas maksimal potongan (Cap)
            if self.max_potongan > 0 and potongan > self.max_potongan:
                potongan = self.max_potongan
        
        # Pastikan diskon tidak melebihi total belanja (supaya tidak minus)
        return min(potongan, total_belanja)

    def clean(self):
        if self.berlaku_mulai and self.berlaku_sampai:
            if self.berlaku_sampai < self.berlaku_mulai:
                raise ValidationError("Tanggal selesai tidak boleh mendahului tanggal mulai.")
        
        if self.tipe_diskon == 'persen' and self.nilai_diskon > 100:
             raise ValidationError("Diskon persen tidak boleh lebih dari 100%.")