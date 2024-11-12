# realtime_data.py

import json
import websocket
import threading
import time
import logging
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from crypto_api import CryptoComAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RealTimeData")

class RealTimeData:
    def __init__(self, symbol: str, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize real-time data handler"""
        self.symbol = symbol
        self.api = CryptoComAPI(api_key, api_secret)
        self.data = pd.DataFrame()
        self.ws = None
        self.ws_thread = None
        self.running = False
        
        # Initialize attributes
        self.short_window = 20
        self.long_window = 50
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        # Setup logger
        self.logger = logging.getLogger("RealTimeData")
        
        # Initialize data structure
        self._initialize_data_structure()
        
    def _initialize_data_structure(self) -> None:
        """Initialize historical data and indicators"""
        try:
            # Get historical klines
            klines = self.api.get_klines(self.symbol)
            
            # Convert klines to DataFrame
            df_data = []
            for kline in klines:
                df_data.append({
                    'timestamp': pd.to_datetime(int(kline['t']), unit='ms'),
                    'open': float(kline['o']),
                    'high': float(kline['h']),
                    'low': float(kline['l']),
                    'close': float(kline['c']),
                    'volume': float(kline['v'])
                })
            
            self.data = pd.DataFrame(df_data)
            self.data.set_index('timestamp', inplace=True)
            
            # Calculate indicators
            self._calculate_indicators()
            
            logger.info(f"Successfully loaded {len(self.data)} historical records")
            
        except Exception as e:
            logger.error(f"Error initializing data structure: {str(e)}")
            raise
            
    def _calculate_indicators(self) -> None:
        """Calculate technical indicators for trading signals"""
        try:
            # Moving Averages
            self.data['SMA_short'] = self.data['close'].rolling(window=self.short_window).mean()
            self.data['SMA_long'] = self.data['close'].rolling(window=self.long_window).mean()
            
            # MACD (12, 26, 9)
            exp1 = self.data['close'].ewm(span=12, adjust=False).mean()
            exp2 = self.data['close'].ewm(span=26, adjust=False).mean()
            self.data['MACD'] = exp1 - exp2
            self.data['Signal_Line'] = self.data['MACD'].ewm(span=9, adjust=False).mean()
            
            # RSI with more aggressive thresholds (25/75 instead of 30/70)
            delta = self.data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            self.data['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands (more sensitive)
            self.data['BB_middle'] = self.data['close'].rolling(window=20).mean()
            std = self.data['close'].rolling(window=20).std()
            self.data['BB_upper'] = self.data['BB_middle'] + (std * 2)
            self.data['BB_lower'] = self.data['BB_middle'] - (std * 2)
            
            # Price Rate of Change (ROC)
            self.data['ROC'] = self.data['close'].pct_change(periods=10) * 100
            
            # Volume Indicators
            self.data['Volume_MA'] = self.data['volume'].rolling(window=20).mean()
            self.data['Volume_Ratio'] = self.data['volume'] / self.data['Volume_MA']
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            raise
            
    def start(self) -> None:
        """Start the WebSocket connection"""
        self.running = True
        self.ws_thread = threading.Thread(target=self._run_websocket)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
    def stop(self) -> None:
        """Stop the WebSocket connection"""
        self.running = False
        if self.ws:
            self.ws.close()
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=1)
            
    def _run_websocket(self) -> None:
        """Run WebSocket connection"""
        try:
            formatted_symbol = self.symbol.replace('-', '_').upper()
            ws_url = "wss://stream.crypto.com/v2/market"
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if 'result' in data and 'data' in data['result']:
                        ticker = data['result']['data'][0]
                        self._process_ticker_data({
                            't': ticker['t'],                    # timestamp
                            'o': ticker['k'],                    # open (using k as current price)
                            'h': ticker['h'],                    # high
                            'l': ticker['l'],                    # low
                            'c': ticker['k'],                    # close (using k as current price)
                            'v': ticker['v']                     # volume
                        })
                        logger.debug(f"Processed ticker: {ticker['k']}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    logger.debug(f"Raw message: {message}")
                    
            def on_error(ws, error):
                logger.error(f"WebSocket error: {str(error)}")
                
            def on_close(ws, close_status_code, close_msg):
                logger.info("WebSocket connection closed")
                if self.running:
                    logger.info("Attempting to reconnect...")
                    time.sleep(5)
                    self.start()
                
            def on_open(ws):
                logger.info("WebSocket connection opened")
                subscribe_message = {
                    "id": 1,
                    "method": "subscribe",
                    "params": {
                        "channels": [f"ticker.{formatted_symbol}"]
                    }
                }
                ws.send(json.dumps(subscribe_message))
                
            # Initialize WebSocket connection
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # Run WebSocket connection
            self.ws.run_forever()
            
        except Exception as e:
            logger.error(f"Error in WebSocket thread: {str(e)}")
            
    def _process_ticker_data(self, ticker_data: Dict[str, Any]) -> None:
        """Process incoming ticker data"""
        try:
            timestamp = pd.to_datetime(int(ticker_data['t']), unit='ms')
            new_data = pd.DataFrame({
                'close': [float(ticker_data['c'])],
                'open': [float(ticker_data['o'])],
                'high': [float(ticker_data['h'])],
                'low': [float(ticker_data['l'])],
                'volume': [float(ticker_data['v'])]
            }, index=[timestamp])
            
            # Update the latest data
            self.data = pd.concat([self.data, new_data])
            self.data = self.data.tail(1000)  # Keep last 1000 records
            
            # Recalculate indicators
            self._calculate_indicators()
            
            # Log the update
            logger.debug(f"Updated price: {ticker_data['c']} at {timestamp}")
            
        except Exception as e:
            logger.error(f"Error processing ticker data: {str(e)}")