import requests
import time
import hmac
import hashlib
import json

API_KEY = "QjD5qQnq7dCvt1gmxTPr83"
API_SECRET = "cxakp_ETe5i18KdeKD73NRXXDGeh"

def test_endpoints():
    base_url = "https://deriv-api.crypto.com/v1"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    
    # Test different DOGE instrument name formats
    test_symbols = [
        "DOGE-USDT",
        "DOGEUSDT",
        "DOGE_USDT",
        "DOGEUSD",
        "DOGE-USD",
        "DOGE_USD"
    ]
    
    print("Testing different DOGE symbol formats...")
    for symbol in test_symbols:
        try:
            params = {
                "instrument_name": symbol,
                "timeframe": "1m"
            }
            response = requests.get(
                f"{base_url}/public/get-candlestick",
                params=params,
                headers=headers,
                timeout=10
            )
            print(f"\nTesting {symbol}:")
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text[:200]}")  # Show first 200 chars
            
        except Exception as e:
            print(f"Error testing {symbol}: {str(e)}")
    
    # Test trading pairs endpoint
    print("\nTesting trading pairs endpoint...")
    try:
        response = requests.get(
            f"{base_url}/public/get-trading-pairs",
            headers=headers,
            timeout=10
        )
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            pairs = data.get('result', {}).get('trading_pairs', [])
            if pairs:
                print("\nAvailable trading pairs:")
                for pair in pairs:
                    print(f"- {pair['symbol']}")
            else:
                print("No trading pairs found")
    except Exception as e:
        print(f"Error getting trading pairs: {str(e)}")

    # Test ticker endpoint
    print("\nTesting ticker endpoint...")
    try:
        response = requests.get(
            f"{base_url}/public/get-ticker",
            headers=headers,
            timeout=10
        )
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            tickers = data.get('result', {}).get('tickers', [])
            if tickers:
                print("\nAvailable tickers:")
                for ticker in tickers:
                    if 'DOGE' in ticker.get('symbol', ''):
                        print(f"- {ticker['symbol']}")
            else:
                print("No tickers found")
    except Exception as e:
        print(f"Error getting tickers: {str(e)}")

if __name__ == "__main__":
    print("Testing Crypto.com Exchange API endpoints...")
    test_endpoints() 