from django.urls import path
from .views import (
    CoinListCreateView,
    CoinDetailView,
    refresh_coin_prices,
    get_coin,
    
    PortfolioListCreateView,
    PortfolioDetailView,
    portfolio_summary,
    portfolio_performance,
    record_portfolio_snapshots,
    PortfolioInsightView,
)

urlpatterns = [
    path('coins/', CoinListCreateView.as_view(), name='coin-list-create'),
    path('coins/<int:pk>/', CoinDetailView.as_view(), name='coin-detail'),
    path('coins/update-prices/', refresh_coin_prices, name='refresh-prices'),
    path('coins/search/<str:coin_id>/', get_coin, name='get-coin'),
    
    path("portfolio/", PortfolioListCreateView.as_view(), name="portfolio-list-create"),
    path("portfolio/<int:pk>/", PortfolioDetailView.as_view(), name="portfolio-detail"),
    path("portfolio/summary/", portfolio_summary, name="portfolio-summary"),
    
    
    
    path("portfolio/<int:portfolio_id>/performance/", portfolio_performance, name="portfolio-performance"),
    path("snapshot/", record_portfolio_snapshots, name="portfolio-snapshot"),
    
    path("insight/", PortfolioInsightView.as_view(), name="insight")

]



