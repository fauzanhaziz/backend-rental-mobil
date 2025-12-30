from rest_framework import serializers
from .models import Mobil

class MobilSerializer(serializers.ModelSerializer):
    """
    Serializer untuk DETAIL & CREATE/UPDATE (Single Object)
    """
    # Menggunakan serializers.SerializerMethodField jauh lebih aman untuk CloudinaryField
    gambar_url = serializers.SerializerMethodField()
    
    transmisi_display = serializers.CharField(source='get_transmisi_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Mobil
        fields = '__all__' 
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_gambar_url(self, obj):
        if obj.gambar:
            return obj.gambar.url # Mengambil link https://res.cloudinary.com/...
        return None

    def validate_plat_nomor(self, value):
        if not value or value.strip() == "":
            return None
        return value


class MobilListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk LIST (Daftar Mobil)
    """
    gambar_url = serializers.SerializerMethodField()
    transmisi_display = serializers.CharField(source='get_transmisi_display', read_only=True)
    
    class Meta:
        model = Mobil
        fields = [
            'id', 'nama_mobil', 'merk', 'jenis', 'plat_nomor', 'tahun',
            'harga_per_hari', 'status', 'gambar_url',
            'transmisi', 'transmisi_display', 'kapasitas_kursi',
            'popularity', 'keterangan',
            'dengan_supir'
        ]

    def get_gambar_url(self, obj):
        if obj.gambar:
            return obj.gambar.url
        return None