from django.utils import timezone
from .models import Pesanan

class AutoCancelZombieOrdersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # --- LOGIKA AUTO CANCEL ---
        # Kita jalankan ini hanya jika request mengarah ke API (agar efisien)
        # dan hanya method GET (saat user mengambil data)
        if request.path.startswith('/api/') and request.method == 'GET':
            try:
                today = timezone.now().date()
                
                # Update massal (Query SQL langsung, sangat cepat)
                # Cari yang 'pending'/'konfirmasi' TAPI tanggal mulainya < hari ini
                rows_updated = Pesanan.objects.filter(
                    status__in=['pending', 'konfirmasi'],
                    tanggal_mulai__lt=today
                ).update(status='batal')
                
                # Opsional: Print di terminal backend kalau ada yang dicancel (untuk debug)
                if rows_updated > 0:
                    print(f"Middleware: {rows_updated} pesanan zombie dibatalkan otomatis.")
                    
            except Exception as e:
                # Jangan sampai error di sini bikin website down
                print(f"Middleware Error: {e}")

        # Lanjutkan request ke view yang dituju
        response = self.get_response(request)
        return response