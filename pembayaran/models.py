from django.db import models
from django.conf import settings
from pesanan.models import Pesanan

class Pembayaran(models.Model):
    METODE_CHOICES = [
        ('transfer', 'Transfer Bank'),
        ('cash', 'Tunai / Cash'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Menunggu Verifikasi'),
        ('lunas', 'Lunas / Terverifikasi'),
        ('gagal', 'Gagal / Ditolak'),
    ]

    # OneToOne: Satu Pesanan hanya punya satu data pembayaran aktif
    pesanan = models.OneToOneField(Pesanan, on_delete=models.CASCADE, related_name='pembayaran')
    
    jumlah = models.DecimalField(max_digits=12, decimal_places=2)
    metode = models.CharField(max_length=20, choices=METODE_CHOICES, default='transfer')
    
    # Bukti bayar (Boleh kosong jika metode = CASH)
    bukti_bayar = models.ImageField(upload_to='bukti_bayar/', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # --- AUDIT TRAIL (Untuk Offline) ---
    # Mencatat siapa Admin yang menerima uang tunai
    dicatat_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='pembayaran_dicatat'
    )
    
    catatan_admin = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pembayaran'
        verbose_name = 'Pembayaran'
        verbose_name_plural = 'Data Pembayaran'

    def __str__(self):
        return f"Pay for {self.pesanan.kode_booking} - {self.status}"