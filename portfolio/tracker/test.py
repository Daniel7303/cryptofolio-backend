from rest_framework.test import APITestCase
from rest_framework import status
from .models import Coin
from decimal import Decimal
from unittest.mock import patch
from tracker.utils import update_coin_prices



class CoinAPITestCase(APITestCase):

    def test_create_coin_success(self):
        data = {"name": "Bitcoin", "symbol": "BTC", "price": "30000.00"}
        response = self.client.post("/api/coins/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Bitcoin")

    def test_list_coins(self):
        Coin.objects.create(name="Ethereum", symbol="ETH", price="2000.00")
        response = self.client.get("/api/coins/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data["results"], list)  # <-- check "results"
        self.assertEqual(len(response.data["results"]), 1)


    def test_retrieve_coin(self):
        coin = Coin.objects.create(name="Litecoin", symbol="LTC", price="100.00")
        response = self.client.get(f"/api/coins/{coin.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["symbol"], "LTC")

    def test_update_coin(self):
        coin = Coin.objects.create(name="Ripple", symbol="XRP", price="0.50")
        data = {"price": "0.60"}
        response = self.client.patch(f"/api/coins/{coin.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["price"]), Decimal("0.60"))

    def test_delete_coin(self):
        coin = Coin.objects.create(name="Dogecoin", symbol="DOGE", price="0.10")
        response = self.client.delete(f"/api/coins/{coin.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Coin.objects.filter(id=coin.id).exists())

    def test_create_coin_missing_name(self):
        data = {"symbol": "ADA", "price": "1.00"}
        response = self.client.post("/api/coins/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        
        
    @patch("tracker.utils.get_coin_prices")
    def test_update_coin_prices(mock_get):
        mock_get.return_value = {"bitcoin": 40000}
        coin = Coin.objects.create(name="Bitcoin", symbol="BTC", price="30000.00")
        update_coin_prices()
        coin.refresh_from_db()
        assert coin.price == Decimal("40000")
    

