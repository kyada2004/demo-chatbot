import requests

# TODO: Replace with your Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = "YOUR_ALPHA_VANTAGE_API_KEY"

def get_stock_price(symbol):
    """Get the current price of a stock."""
    if ALPHA_VANTAGE_API_KEY == "YOUR_ALPHA_VANTAGE_API_KEY":
        return "Please replace the placeholder Alpha Vantage API key in app/features/stock.py"

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        quote = data.get("Global Quote")
        if not quote or not quote.get("05. price"):
            return f"I couldn't find the stock price for {symbol}."

        return f"The current price of {symbol} is ${quote['05. price']}."

    except requests.exceptions.RequestException as e:
        print(f"[Stock API Error] {e}")
        return "I encountered an error while trying to fetch the stock price."
