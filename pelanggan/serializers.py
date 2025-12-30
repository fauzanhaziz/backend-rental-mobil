from rest_framework import serializers
from .models import Pelanggan

class PelangganSerializer(serializers.ModelSerializer):
    # Field tambahan untuk URL lengkap
    foto_ktp_url = serializers.SerializerMethodField()
    foto_sim_url = serializers.SerializerMethodField()
    status_akun = serializers.SerializerMethodField()

    class Meta:
        model = Pelanggan
        fields = [
            'id', 'user', 'nama', 'no_hp', 'alamat', 
            'ktp', 
            'foto_ktp',      # <--- Field asli untuk Upload (Write)
            'foto_ktp_url',  # <--- Field helper untuk Menampilkan URL (Read)
            'foto_sim', 
            'foto_sim_url', 
            'catatan', 'status_akun', 'created_at'
        ]
        read_only_fields = ['user', 'created_at', 'foto_ktp_url', 'foto_sim_url']

    def get_status_akun(self, obj):
        return "Online" if obj.user else "Offline"

    # --- PERBAIKAN DI SINI ---
    # Nama method harus: get_<nama_field>
    def get_foto_ktp_url(self, obj):
        # Akses ke obj.foto_ktp (sesuai model baru)
        if obj.foto_ktp:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.foto_ktp.url)
            return obj.foto_ktp.url
        return None

    def get_foto_sim_url(self, obj):
        if obj.foto_sim:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.foto_sim.url)
            return obj.foto_sim.url
        return None