from rest_framework import serializers
from .models import Alert

class AlertSerializer(serializers.ModelSerializer):
    coin_name = serializers.CharField(source='coin.name', read_only=True)
    current_price = serializers.DecimalField(source='coin.price', read_only=True, max_digits=20, decimal_places=8)

    class Meta:
        model = Alert
        fields = [
            'id', 'coin', 'coin_name', 'current_price', 
            'alert_type', 'target_price', 
            'triggered', 'triggered_at', 'created_at', 'message'
        ]
        read_only_fields = ['triggered', 'triggered_at', 'created_at', 'message']
