import os   
from django.db import models
from django.conf import settings
from users.validators import validate_indonesian_nik

def upload_location(instance, filename):
    # 1. Ambil ekstensi file (jpg/png)
    file_extension = filename.split('.')[-1]
    
    # 2. Ambil username untuk nama file yang unik
    # Menggunakan f-string agar aman jika user None
    username = instance.user.username if instance.user else f"offline_{instance.nama}"
    clean_username = "".join(x for x in username if x.isalnum())
    
    # 3. Buat nama file baru
    new_filename = f"ktp_{clean_username}.{file_extension}"
    
    # 4. Return path lengkap
    return f"pelanggan/{new_filename}"

class Pelanggan(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pelanggan',
        null=True,
        blank=True
    )
    
    nama = models.CharField(max_length=100)
    no_hp = models.CharField(max_length=20)
    alamat = models.TextField(blank=True, null=True)
    
    ktp = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        validators=[validate_indonesian_nik],
        help_text="Harus 16 digit sesuai KTP"
    )
    
    # --- PERBAIKAN DI SINI ---
    foto_ktp = models.ImageField(
        upload_to=upload_location,  # <--- WAJIB TAMBAHKAN INI
        blank=True, 
        null=True,
        help_text="Foto KTP Asli"
    )
    
    foto_sim = models.ImageField(upload_to='pelanggan/sim/', blank=True, null=True)
    
    catatan = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pelanggan'
        ordering = ['-created_at']
        verbose_name = 'Pelanggan'
        verbose_name_plural = 'Data Pelanggan'

    def __str__(self):
        tipe = "Online" if self.user else "Offline"
        return f"{self.nama} ({tipe})"

    def delete(self, *args, **kwargs):
        if self.foto_ktp:
            self.foto_ktp.delete(save=False)
        if self.foto_sim:
            self.foto_sim.delete(save=False)
        super().delete(*args, **kwargs)