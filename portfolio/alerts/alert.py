from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response
from .models import Alert
import requests
from decimal import Decimal

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_alerts(request):
    alerts = Alert.objects.filter(user=request.user, triggered=False)
    triggered_alerts = []

    for alert in alerts:
        cg_id = alert.coin.coingecko_id
        price_url = f"{COINGECKO_BASE}/simple/price?ids={cg_id}&vs_currencies=usd"
        resp = requests.get(price_url)

        if resp.status_code != 200:
            continue

        data = resp.json()
        current_price = data.get(cg_id, {}).get("usd")
        if not current_price:
            continue

        current_price = Decimal(str(current_price))
        target_price = Decimal(str(alert.target_price))
        tolerance = target_price * Decimal("0.001")  # 0.1% tolerance range

        # Check if within tolerance range (≈ target)
        if abs(current_price - target_price) <= tolerance:
            alert.trigger()  # use your model’s trigger() method
            triggered_alerts.append({
                "coin": alert.coin.name,
                "target": float(target_price),
                "current": float(current_price),
                "message": alert.message or f"{alert.coin.name} reached approximately ${target_price:.2f}!",
            })

    if not triggered_alerts:
        return Response({"message": "No alerts triggered yet."}, status=status.HTTP_200_OK)

    return Response({"triggered": triggered_alerts}, status=status.HTTP_200_OK)
