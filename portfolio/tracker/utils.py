import requests
from decimal import Decimal
from .models import Coin
from django.utils.timezone import now
from .models import Portfolio, PortfolioHistory



def get_coin_prices(coin_ids):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids":",".join(coin_ids), "vs_currencies": "usd"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return {k: v['usd'] for k, v in response.json().items()}


def update_coin_prices():
    coins = Coin.objects.all()
    if not coins:
        print("No coins in DB. Run populate_top_coins first.")
        return

    coin_ids = [coin.coingecko_id for coin in coins]
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(coin_ids), "vs_currencies": "usd"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    prices = response.json()

    for coin in coins:
        if coin.coingecko_id in prices:
            coin.price = Decimal(str(prices[coin.coingecko_id]["usd"]))
            coin.save()
            print(f"Updated {coin.name} (${coin.price})")

            
            

# tracker/utils.py
import requests
from decimal import Decimal
from .models import Coin

def get_top_coins(n=100):
    """
    Fetch top `n` coins by market cap from CoinGecko.
    Returns a list of coin IDs.
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": n,
        "page": 1,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching top coins: {e}")
        return []

    data = response.json()
    return data  # return full data, not just IDs



def populate_top_coins(n=100):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": n, "page": 1}
    response = requests.get(url, params=params)
    response.raise_for_status()
    coins_data = response.json()

    for coin_data in coins_data:
        coin, created = Coin.objects.update_or_create(
            coingecko_id=coin_data["id"],  # Use unique ID
            defaults={
                "name": coin_data["name"],
                "symbol": coin_data["symbol"].upper(),
                "price": Decimal(str(coin_data["current_price"]))
            }
        )
        action = "Created" if created else "Updated"
        print(f"{action} {coin.name} ({coin.symbol}) - ${coin.price}")


def fetch_coin_on_demand(coin_id):
    from .models import Coin
    try:
        # check DB first by CoinGecko ID
        return Coin.objects.get(coingecko_id__iexact=coin_id)
    except Coin.DoesNotExist:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id.lower()}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            coin = Coin.objects.create(
                coingecko_id=data["id"],
                name=data["name"],
                symbol=data["symbol"].upper(),
                price=Decimal(str(data["market_data"]["current_price"]["usd"]))
            )
            return coin
        return None


def record_portfolio_snapshots():
    today = now().date()
    portfolios = Portfolio.objects.all()

    for p in portfolios:
        if p.coin and p.coin.price:
            value = float(p.amount) * float(p.coin.price)
            PortfolioHistory.objects.update_or_create(
                portfolio=p,
                date=today,
                defaults={"value_usd": value}
            )
