import os
from django.db import models
from cloudinary.models import CloudinaryField  # <--- 1. WAJIB IMPORT INI

class HeroSection(models.Model):
    judul = models.CharField(max_length=200, help_text="Judul besar di tengah layar")
    sub_judul = models.TextField(blank=True, null=True, help_text="Deskripsi singkat di bawah judul")
    
    # 2. GANTI BAGIAN INI (Mendukung Foto & Video)
    background_media = CloudinaryField(
        'image', 
        folder='website/hero', 
        resource_type='auto', # 'auto' artinya bisa upload Video ATAU Gambar
        help_text="Upload Video (mp4/webm) atau Gambar (jpg/png)"
    )
    
    is_active = models.BooleanField(default=True, help_text="Jika dicentang, slide ini akan tampil")
    urutan = models.IntegerField(default=0, help_text="Angka lebih kecil tampil lebih dulu")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Konfigurasi Hero"
        verbose_name_plural = "Konfigurasi Hero"
        ordering = ['urutan', '-created_at']

    def __str__(self):
        return self.judul

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Dokumentasi(models.Model):
    judul = models.CharField(max_length=200, help_text="Judul kegiatan/foto")
    deskripsi = models.TextField(blank=True, null=True, help_text="Cerita singkat dibalik foto/video ini")
    
    # 3. GANTI BAGIAN INI JUGA
    file_media = CloudinaryField(
        'image', 
        folder='website/dokumentasi', 
        resource_type='auto', # Penting agar bisa upload video dokumentasi
        help_text="Upload Foto (.jpg/.png) atau Video (.mp4)"
    )
    
    urutan = models.IntegerField(default=0, help_text="Urutan tampilan (0 paling awal)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Galeri Dokumentasi"
        verbose_name_plural = "Galeri Dokumentasi"
        ordering = ['urutan', '-created_at']

    def __str__(self):
        return self.judul