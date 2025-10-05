from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Q

# DRF modules
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions
from rest_framework.exceptions import ValidationError


import requests

# App modules
from accounts.permissions import IsOwner
from .models import Coin, Portfolio, PortfolioHistory, Watchlist
from .serializers import CoinSerializer, PortfolioSerializer, WatchlistSerializer
from .utils import update_coin_prices
from .utils import fetch_coin_on_demand
from . pagination import StandardResultSetPagination


# Create your views here.

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


class CoinListView(generics.ListAPIView):
    queryset = Coin.objects.all()
    serializer_class = CoinSerializer
    
    # permission_classes = [IsAuthenticated]
    pagination_class = StandardResultSetPagination
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "symbol"]
    ordering_fields = ["price", "name"]
    
    
    
    
class CoinDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coin.objects.all()
    serializer_class = CoinSerializer

class WatchlistListCreateView(generics.ListCreateAPIView):
    
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Watchlist.objects.all()
        return Watchlist.objets.filter(user=user)
    
    def perform_create(self, serializer):
        user = self.request.user
        coin = serializer.validated_data["coin"]
                                         
        if Watchlist.objects.filter(user=user, coin=coin).exists():
            raise ValidationError("Coin already exists in your watchlist.")
        serializer.save(user=self.request.user)


class WatchlistDetailView(generics.DestroyAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Watchlist.objects.all()
        return Watchlist.objects.filter(user=user)



@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
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
def search_coin(request):
    query = request.GET.get("query", "").strip()
    if not query:
        return Response({"error": "Query parameter is required"}, status=400)

    # 1. Check local DB
    local_matches = Coin.objects.filter(
        Q(name__icontains=query) | Q(symbol__icontains=query)
    )
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
    for c in coins[:5]:  # limit to top 5 results
        cg_id = c["id"]
        detail_url = f"{COINGECKO_BASE}/coins/{cg_id}"
        detail_resp = requests.get(detail_url)

        if detail_resp.status_code != 200:
            continue

        detail = detail_resp.json()
        price = detail.get("market_data", {}).get("current_price", {}).get("usd", 0)

        coin, _ = Coin.objects.update_or_create(
            coingecko_id=cg_id,
            defaults={
                "name": detail["name"],
                "symbol": detail["symbol"].upper(),
                "price": price,
            },
        )
        results.append(CoinSerializer(coin).data)

    return Response(results)





class PortfolioListCreateView(generics.ListCreateAPIView):
    # queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    
    permission_classes = [permissions.IsAuthenticated]
    
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Portfolio.objects.all()
        
        return Portfolio.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # serializer.save(user=self.request.user)
        portfolio = serializer.save(user=self.request.user)
        # take first snapshot
        PortfolioHistory.objects.create(
            portfolio=portfolio,
            value_usd=portfolio.amount * portfolio.coin.price
        )
    

class PortfolioDetailView(generics.RetrieveUpdateDestroyAPIView):
    # queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Portfolio.objects.all()
        
        return Portfolio.objects.filter(user=self.request.user)
        
    
    

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
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
    
    portfolio = Portfolio.objects.get(id=portfolio_id)
    if not (request.user.is_staff or portfolio.user == request.user):
        return Response({"error": "Forbidden"}, status=403)

    try:
        history = PortfolioHistory.objects.filter(portfolio_id=portfolio_id).order_by("date")
        if not history.exists():
            return Response({"Error": "No History yet"})

        first = history.first()
        portfolio = first.portfolio  
    
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
@permission_classes([permissions.IsAdminUser])
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



@permission_classes([permissions.IsAuthenticated])
class PortfolioInsightView(APIView):
    def get(self, request):
        portfolio = Portfolio.objects.filter(user=request.user).select_related("coin")
        holdings = []
        total_value = 0
        
        for p in portfolio:
            value = float(p.amount) * float(p.coin.price)
            holdings.append({
                "coin": p.coin.name,
                "quantity": float(p.amount),
                "price": float(p.coin.price),
                'value':value
            })
            
            total_value += value
            
        for h in holdings:
            h["percentage"] = (h["value"] / total_value * 100) if total_value > 0 else 0
            
        
        top_holding = max(holdings, key=lambda x: x["value"], default=None)
        
        
        data = {
            "total_value_usd": total_value,
            "number_of_assets": len(holdings),
            "top_holding": top_holding,
            "holdings": holdings
            
        }
        
        return Response(data)