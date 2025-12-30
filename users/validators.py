import datetime
from django.core.exceptions import ValidationError

def validate_indonesian_nik(value: str):
    """
    Validasi NIK Indonesia:
    1. Harus 16 digit angka.
    2. 6 digit pertama adalah kode wilayah (kita hanya cek numeric).
    3. Digit 7-12 adalah tanggal lahir (DDMMYY).
       - Wanita: Tanggal + 40 (misal tgl 1 jadi 41).
    """
    if not value.isdigit():
        raise ValidationError("NIK harus berupa angka.")
    
    if len(value) != 16:
        raise ValidationError("NIK harus terdiri dari 16 digit.")

    # Parsing Tanggal Lahir dari NIK
    # Format: PP.KK.CC.DDMMYY.SSSS
    try:
        hari = int(value[6:8])
        bulan = int(value[8:10])
        tahun = int(value[10:12])

        # Koreksi tanggal untuk Wanita (Tanggal + 40)
        if hari > 40:
            hari = hari - 40

        # Estimasi tahun (NIK tidak ada 4 digit tahun)
        # Asumsi: Penyewa mobil pasti lahir antara 1900 - 2024
        # Logic sederhana: Jika > 24, anggap 19xx. Jika <= 24, anggap 20xx
        # (Ini bisa disesuaikan kebutuhan)
        current_year_short = int(datetime.datetime.now().strftime("%y"))
        full_year = 2000 + tahun if tahun <= current_year_short else 1900 + tahun

        # Coba convert ke date object, kalau invalid (misal bulan 13), akan error
        datetime.date(full_year, bulan, hari)

    except ValueError:
        raise ValidationError("Format tanggal lahir pada NIK tidak valid.")
    
    except Exception:
        raise ValidationError("NIK tidak valid.")