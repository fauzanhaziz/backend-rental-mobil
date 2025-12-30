from django.db import models

class Supir(models.Model):
    STATUS_CHOICES = [
        ('tersedia', 'Tersedia / Standby'),
        ('bertugas', 'Sedang Bertugas'),
        ('off', 'Libur / Off'),
    ]

    nama = models.CharField(max_length=100)
    no_hp = models.CharField(max_length=20)
    
    # Harga jasa supir per hari (Default standard rental, misal 150rb)
    harga_per_hari = models.DecimalField(max_digits=12, decimal_places=2, default=150000)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='tersedia')
    foto = models.ImageField(upload_to='supir/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'supir'
        ordering = ['nama']
        verbose_name = 'Supir'
        verbose_name_plural = 'Data Supir'

    def __str__(self):
        return f"{self.nama} ({self.get_status_display()})"