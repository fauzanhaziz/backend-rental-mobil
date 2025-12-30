from rest_framework import serializers
from .models import Promo

class PromoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promo
        fields = [
            'id', 'kode', 'nama_promo', 'keterangan', 
            'tipe_diskon', 'nilai_diskon', 'max_potongan', # Field baru
            'min_transaksi', 
            'berlaku_mulai', 'berlaku_sampai'
        ]