from rest_framework import serializers
from django.utils.timezone import now
from .models import Coin, Portfolio, PortfolioHistory


class CoinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coin
        fields = "__all__"

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value


class PortfolioHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioHistory
        fields = ["date", "value_usd"]


class PortfolioSerializer(serializers.ModelSerializer):
    # relationships
    coin = CoinSerializer(read_only=True)
    coin_id = serializers.PrimaryKeyRelatedField(
        queryset=Coin.objects.all(), source="coin", write_only=True
    )

    # computed fields
    initial_value = serializers.SerializerMethodField()
    current_value = serializers.SerializerMethodField()
    usd_growth = serializers.SerializerMethodField()
    pct_growth = serializers.SerializerMethodField()
    history = PortfolioHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            "id",
            "coin",
            "coin_id",
            "amount",
            "initial_value",
            "current_value",
            "usd_growth",
            "pct_growth",
            "history",
        ]

    def get_initial_value(self, obj):
        first_snapshot = obj.history.order_by("date").first()
        return float(first_snapshot.value_usd) if first_snapshot else None

    def get_current_value(self, obj):
        live_price = obj.coin.price if obj.coin else 0
        return float(obj.amount) * float(live_price)

    def get_usd_growth(self, obj):
        initial_value = self.get_initial_value(obj)
        current_value = self.get_current_value(obj)
        if initial_value is None:
            return 0
        return current_value - initial_value

    def get_pct_growth(self, obj):
        initial_value = self.get_initial_value(obj)
        current_value = self.get_current_value(obj)
        if not initial_value or initial_value == 0:
            return 0
        return ((current_value - initial_value) / initial_value) * 100

    def create(self, validated_data):
    # validated_data["coin"] is a Coin instance here
        portfolio = Portfolio.objects.create(**validated_data)

        # record first snapshot
        if portfolio.coin and portfolio.coin.price:
            value = float(portfolio.amount) * float(portfolio.coin.price)
            PortfolioHistory.objects.create(
                portfolio=portfolio,
                date=now().date(),
                value_usd=value,
            )
        return portfolio



 #adding portfolio insight serializers
 
# class PortfolioInsightSerializer(serializers.Serializer):
#     total_value_usd = serializers.FloatField()
#     number_of_assets = serializers.IntegerField()
#     top_holding = serializers.DictField()
#     holddings = serializers.ListField()