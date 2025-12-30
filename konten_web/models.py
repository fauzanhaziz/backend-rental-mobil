import os
from django.db import models

class HeroSection(models.Model):
    judul = models.CharField(max_length=200, help_text="Judul besar di tengah layar")
    sub_judul = models.TextField(blank=True, null=True, help_text="Deskripsi singkat di bawah judul")
    
    background_media = models.FileField(
        upload_to='website/hero/', 
        help_text="Upload Video (mp4/webm) atau Gambar (jpg/png)"
    )
    
    is_active = models.BooleanField(default=True, help_text="Jika dicentang, slide ini akan tampil")
    
    # Field Urutan (Penting untuk Slider)
    urutan = models.IntegerField(default=0, help_text="Angka lebih kecil tampil lebih dulu")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Konfigurasi Hero"
        verbose_name_plural = "Konfigurasi Hero"
        ordering = ['urutan', '-created_at'] # Mengurutkan otomatis berdasarkan angka urutan

    def __str__(self):
        return self.judul

    def save(self, *args, **kwargs):
        # PENTING: Jangan ada logika mematikan hero lain di sini.
        # Biarkan standar agar bisa banyak hero aktif sekaligus (Carousel).
        super().save(*args, **kwargs)


class Dokumentasi(models.Model):
    judul = models.CharField(max_length=200, help_text="Judul kegiatan/foto")
    deskripsi = models.TextField(blank=True, null=True, help_text="Cerita singkat dibalik foto/video ini")
    
    file_media = models.FileField(
        upload_to='website/dokumentasi/', 
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