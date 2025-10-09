from django.db import models
from django.conf import settings
from tracker.models import Coin  # adjust import if needed
from django.utils import timezone

class Alert(models.Model):
    ALERT_TYPES = [
        ('price', 'Price Alert'),
        ('portfolio', 'Portfolio Alert'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alerts')
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default='price')
    target_price = models.DecimalField(max_digits=20, decimal_places=8)
    triggered = models.BooleanField(default=False)
    triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True, null=True)

    def trigger(self):
        """Mark this alert as triggered and set a message."""
        self.triggered = True
        self.triggered_at = timezone.now()
        self.message = f"{self.coin.name} has reached ${self.target_price}!"
        self.save()

    def __str__(self):
        return f"{self.coin.symbol} Alert @ {self.target_price}"
