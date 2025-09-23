from django.db import models
from decimal import Decimal
from django.utils.timezone import now



# Create your models here.


class Coin(models.Model):
    coingecko_id = models.CharField(max_length=50, null=True, unique=True)  
    name = models.CharField(max_length=100,)
    symbol = models.CharField(max_length=10, unique=False)
    price = models.DecimalField(max_digits=20, decimal_places=8, )
    date_created = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"
    
    
    
class Portfolio(models.Model):
    name  = models.CharField(max_length=100)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE, related_name="holdings")
    amount = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal("0.0"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    @property
    def value(self):
        """Return holding value in USD"""
        
        return self.amount * (self.coin.price or Decimal("0.0"))
    
    def __str__(self):
        return f"{self.name} {self.coin.symbol}"
    
    
    

class PortfolioHistory(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="history")
    date = models.DateField(default=now)
    value_usd = models.DecimalField(max_digits=20, decimal_places=2)
    
    
    class Meta:
        unique_together = ("portfolio", "date")
        
    def __str__(self):
        return f"{self.portfolio.coin.symbol} - {self.date} - ${self.value_usd}"
    
    
    @property
    def usd_growth(self):
        first = PortfolioHistory.objects.filter(portfolio=self.portfolio).order_by("date").first()
        if first:
            return float(self.value_usd) - float(first.value_usd)
        return 0
    
    
    
    @property
    def pct_growth(self):
        first = PortfolioHistory.objects.filter(Portfolio=self.portfolio).order_by("date").first()
        if first and float(first.value_usd) > 0:
            return (float(self.value_usd) - float(first.value_usd)) / float(first.value_usd) * 100
        return 0
    
    
    
    
    
    