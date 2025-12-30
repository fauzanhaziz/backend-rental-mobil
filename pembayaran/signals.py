from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Pembayaran

@receiver(post_save, sender=Pembayaran)
def update_status_pesanan(sender, instance, created, **kwargs):
    """
    Signal ini berjalan OTOMATIS setiap kali tabel Pembayaran di-save.
    Tujuannya: Menyelaraskan status Pembayaran dengan Pesanan.
    """
    try:
        # Ambil objek pesanan terkait
        pesanan = instance.pesanan
        
        # LOGIKA 1: Jika Pembayaran LUNAS -> Pesanan jadi KONFIRMASI (Siap Jalan)
        if instance.status == 'lunas':
            # Cek agar tidak menimpa status 'selesai' atau 'batal'
            if pesanan.status not in ['selesai', 'batal']:
                pesanan.status = 'konfirmasi'
                pesanan.save()
                print(f"✅ SIGNAL: Pesanan {pesanan.kode_booking} otomatis di-update ke KONFIRMASI.")

        # LOGIKA 2: Jika Pembayaran DITOLAK/GAGAL -> Pesanan kembali PENDING
        elif instance.status == 'gagal':
            if pesanan.status == 'konfirmasi':
                pesanan.status = 'pending'
                pesanan.save()
                print(f"⚠️ SIGNAL: Pembayaran gagal. Pesanan {pesanan.kode_booking} kembali ke PENDING.")
                
    except Exception as e:
        print(f"❌ SIGNAL ERROR: {e}")