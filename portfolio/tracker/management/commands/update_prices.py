from django.core.management.base import BaseCommand
from tracker.utils import update_coin_prices

class Command(BaseCommand):
    help = "Update coin prices from CoinGecko"

    def handle(self, *args, **kwargs):
        update_coin_prices()
        self.stdout.write(self.style.SUCCESS("Coin prices updated successfully!"))
