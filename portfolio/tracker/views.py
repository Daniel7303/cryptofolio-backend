from django.shortcuts import render
from django.utils.timezone import now

# DRF modules
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests

# App modules
from .models import Coin, Portfolio, PortfolioHistory
from .serializers import CoinSerializer, PortfolioSerializer
from .utils import update_coin_prices
from .utils import fetch_coin_on_demand

# Create your views here.

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


class CoinListCreateView(generics.ListCreateAPIView):
    queryset = Coin.objects.all()
    serializer_class = CoinSerializer
    
    #addng filters
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "symbol"]
    ordering_fields = ["price", "name"]
    
    
    
    
class CoinDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coin.objects.all()
    serializer_class = CoinSerializer
    

@api_view(["POST"])
def refresh_coin_prices(request):
    try:
        update_coin_prices()
        return Response({"message": "Coin prices updated successfully!"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(["GET"])
def get_coin(request, coin_id):
    coin = fetch_coin_on_demand(coin_id)
    if coin:
        return Response({
            "name": coin.name,
            "symbol": coin.symbol,
            "price": str(coin.price)
        })
    return Response({"error": "Coin not found"}, status=404)


@api_view(["GET"])
def search_coin(request, query):
    # 1. Check local DB by name OR symbol
    local_matches = Coin.objects.filter(name__icontains=query) | Coin.objects.filter(symbol__icontains=query)
    if local_matches.exists():
        serializer = CoinSerializer(local_matches, many=True)
        return Response(serializer.data)

    # 2. Search CoinGecko
    search_url = f"{COINGECKO_BASE}/search?query={query}"
    resp = requests.get(search_url)
    if resp.status_code != 200:
        return Response({"error": "Failed to fetch from CoinGecko"}, status=500)

    data = resp.json()
    coins = data.get("coins", [])
    if not coins:
        return Response({"error": "Coin not found"}, status=404)

    results = []
    for c in coins:
        cg_id = c["id"]  # e.g. "terra-luna-2"
        detail_url = f"{COINGECKO_BASE}/coins/{cg_id}"
        detail_resp = requests.get(detail_url)

        if detail_resp.status_code != 200:
            continue

        detail = detail_resp.json()
        price = detail.get("market_data", {}).get("current_price", {}).get("usd", None)

        # Use coingecko_id to guarantee uniqueness
        coin, created = Coin.objects.update_or_create(
            coingecko_id=cg_id,
            defaults={
                "name": detail["name"],
                "symbol": detail["symbol"].upper(),
                "price": price or 0
            }
        )

        results.append(CoinSerializer(coin).data)

    return Response(results)





class PortfolioListCreateView(generics.ListCreateAPIView):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    
    def perform_create(self, serializer):
        portfolio = serializer.save(user=self.request.user)
        # take first snapshot when coin is added
        PortfolioHistory.objects.create(
            portfolio=portfolio,
            value_usd=portfolio.amount * portfolio.coin.price
        )
    

class PortfolioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer

@api_view(["GET"])
def portfolio_summary(request):
    Portfolios = Portfolio.objects.all()
    total_value = 0
    breakdown = []
    
    for p in Portfolios:
        if p.coin and p.coin.price:
            value = float(p.amount) * float(p.coin.price)
            total_value += value
            breakdown.append({
                "coin": p.coin.name,
                "symbol": p.coin.symbol.upper(),
                "amount": float(p.amount),
                "value_usd": value,
            })
            
    breakdown.sort(key=lambda x: x["value_usd"], reverse=True)
    
    return Response({
        "total_value_usd": total_value,
        "holdings_count": Portfolios.count(),
        "breakdown": breakdown,
        
    })
    



@api_view(["GET"])
def portfolio_performance(request, portfolio_id):
    try:
        history = PortfolioHistory.objects.filter(portfolio_id=portfolio_id).order_by("date")
        if not history.exists():
            return Response({"Error": "No History yet"})

        first = history.first()
        portfolio = first.portfolio  # same portfolio for all history

        # use live price
        current_value = float(portfolio.amount) * float(portfolio.coin.price)

        return Response({
            "coin": portfolio.coin.symbol,
            "current_price": portfolio.coin.price,
            "initial_value": float(first.value_usd),
            "current_value": current_value,
            "usd_growth": current_value - float(first.value_usd),
            "pct_growth": (
                ((current_value - float(first.value_usd)) / float(first.value_usd)) * 100
                if float(first.value_usd) > 0 else 0
            ),
            "history": [
                {"date": h.date, "value_usd": float(h.value_usd)}
                for h in history
            ]
        })
    except PortfolioHistory.DoesNotExist:
        return Response({"error": "Portfolio not found"}, status=404)






@api_view(["POST"])
def record_portfolio_snapshots(request):
    portfolios = Portfolio.objects.all()
    snapshots = []

    for p in portfolios:
        if p.coin and p.coin.price:
            value = float(p.amount) * float(p.coin.price)
            snapshot, created = PortfolioHistory.objects.get_or_create(
                portfolio=p,
                date=now().date(),
                defaults={"value_usd": value}
            )
            if not created:
                snapshot.value_usd = value
                snapshot.save()
            snapshots.append({
                "portfolio": p.id,
                "coin": p.coin.symbol,
                "value_usd": value
            })

    return Response({"snapshots": snapshots})
