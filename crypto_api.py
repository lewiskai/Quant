import requests
import json
import hmac
import hashlib
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CryptoComAPI:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize Crypto.com API client"""
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.crypto.com/v2"
        
    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for Crypto.com API (e.g., DOGE-USD -> DOGE_USDT)"""
        # Remove any existing separators and convert to uppercase
        clean_symbol = symbol.replace('-', '').replace('_', '').upper()
        
        # If symbol ends with USD, replace with USDT
        if clean_symbol.endswith('USD'):
            clean_symbol = clean_symbol[:-3] + '_USDT'
        else:
            # Add underscore between currency pairs
            clean_symbol = clean_symbol[:-3] + '_' + clean_symbol[-3:]
            
        return clean_symbol
        
    def get_klines(self, symbol: str, timeframe: str = "1m", limit: int = 1000) -> Dict:
        """
        Get historical kline/candlestick data from Crypto.com
        
        Args:
            symbol: Trading pair (e.g., 'DOGE-USD')
            interval: Timeframe ('1m', '5m', '15m', '30m', '1h', '4h', '6h', '12h', '1d', '1w', '1M')
            limit: Number of candles to return
            
        Returns:
            Dict containing kline data
        """
        try:
            formatted_symbol = self._format_symbol(symbol)
            logger.debug(f"Formatted symbol: {formatted_symbol}")
            
            endpoint = "/public/get-candlestick"
            params = {
                "instrument_name": formatted_symbol,
                "timeframe": timeframe,
                "count": limit
            }
            
            logger.debug(f"Requesting klines with params: {params}")
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=10
            )
            
            response.raise_for_status()  # Raises HTTPError for bad responses
            data = response.json()
            if 'result' not in data:
                raise KeyError("Missing 'result' in API response")
            return data['result']['data']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error occurred: {e}")
            raise
        except KeyError as e:
            self.logger.error(f"Key error: {e}")
            raise
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise
            
    def get_ticker(self, symbol: str) -> Dict:
        """Get latest ticker data from Crypto.com"""
        try:
            formatted_symbol = self._format_symbol(symbol)
            
            endpoint = "/public/get-ticker"
            params = {"instrument_name": formatted_symbol}
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code}")
                
            data = response.json()
            
            if data.get('code') != 0:
                raise Exception(f"API error: {data.get('msg', 'Unknown error')}")
                
            return data['result']['data']
            
        except Exception as e:
            logger.error(f"Error fetching ticker: {str(e)}")
            raise
