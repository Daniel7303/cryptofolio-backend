from django.contrib import admin
from . models import Coin, Portfolio

# Register your models here.

@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'price', 'date_created')
    search_fields = ("name", "symbol")
    


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("coin", "amount", "created_at")
    list_filter = ("coin", "created_at")
    search_fields = ("coin__name", "coin__symbol")