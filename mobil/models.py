from django.db import models

class Mobil(models.Model):
    STATUS_CHOICES = [
        ('aktif', 'Aktif / Siap Sewa'),
        ('servis', 'Sedang Servis / Bengkel'),
        ('nonaktif', 'Non-Aktif / Arsip'),
    ]
    
    TRANSMISI_CHOICES = [
        ('manual', 'Manual'),
        ('matic', 'Automatic'),
    ]

    # --- TAMBAHKAN OPSI POPULARITAS DISINI ---
    POPULARITY_CHOICES = [
        ('standard', 'Standard'),
        ('bestseller', 'Best Seller'),
        ('hotdeal', 'Hot Deal'),
        ('new', 'New Arrival'),
        ('recommended', 'Rekomendasi'),
    ]

    nama_mobil = models.CharField(max_length=100)
    merk = models.CharField(max_length=100, blank=True, null=True)
    jenis = models.CharField(max_length=50, blank=True, null=True)
    plat_nomor = models.CharField(max_length=20, unique=True, null=True, blank=True)
    tahun = models.IntegerField(null=True, blank=True)
    transmisi = models.CharField(max_length=10, choices=TRANSMISI_CHOICES, default='manual')
    kapasitas_kursi = models.IntegerField(default=4)
    dengan_supir = models.BooleanField(default=False, help_text="Ceklis jika harga sudah termasuk supir (All In)")
    harga_per_hari = models.DecimalField(max_digits=12, decimal_places=2)
    denda_per_jam = models.DecimalField(max_digits=12, decimal_places=2, default=50000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aktif')
    
    # --- FIELD BARU ---
    popularity = models.CharField(
        max_length=20, 
        choices=POPULARITY_CHOICES, 
        default='standard',
        help_text="Label marketing untuk mobil ini"
    )
    
    gambar = models.ImageField(upload_to='mobil/', blank=True, null=True)
    keterangan = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mobil'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nama_mobil} - {self.plat_nomor}"