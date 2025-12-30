from rest_framework import serializers
from .models import Supir

class SupirSerializer(serializers.ModelSerializer):
    foto_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Supir
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_foto_url(self, obj):
        if obj.foto:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.foto.url)
        return None