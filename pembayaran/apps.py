from django.apps import AppConfig

class PembayaranConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pembayaran'

    def ready(self):
        # Import signals di sini agar aktif saat Django start
        import pembayaran.signals