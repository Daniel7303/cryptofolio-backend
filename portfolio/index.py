# import requests

# url = "http://127.0.0.1:8000/api/coins/"

# response = requests.get(url)

# print(response.json())

# data = response.json()

# for key, value in data.items():
#     print("bitcoin":, data[bitcoin])


import requests

url = "http://127.0.0.1:8000/api/coins/"

response = requests.get(url)
data = response.json()

coins = data.get("results", [])

btc_price = next((coin["price"] for coin in coins if coin["symbol"].upper() == "ETH"), "Not available")

print("ETH",btc_price)