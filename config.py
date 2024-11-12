# config.py

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Trading pair information
TICKER = 'DOGE-USD'  # Yahoo Finance format
BINANCE_SYMBOL = 'dogeusdt'  # Binance format

# API credentials
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

# Data time range
START_DATE = '2020-01-01'
END_DATE = '2024-11-11'

# Strategy parameters
SHORT_WINDOW = 20  # Short-term MA window
LONG_WINDOW = 50  # Long-term MA window

# Logging configuration
LOG_FILE = 'trading_log.txt'
LOG_LEVEL = 'DEBUG'

# Trading parameters
TRADE_AMOUNT = 100  # USDT amount per trade
STOP_LOSS_PERCENT = 2.0
TAKE_PROFIT_PERCENT = 4.0
MAX_POSITIONS = 3

# WebSocket configuration
WEBSOCKET_TIMEOUT = 30
WEBSOCKET_RETRY = 3
WEBSOCKET_RECONNECT = True
WEBSOCKET_PING_INTERVAL = 30
WEBSOCKET_PING_TIMEOUT = 10

# Trading configuration
TRADE_CONFIG = {
    'max_daily_trades': 10,
    'min_profit_target': 1.5,
    'max_spread': 0.1,
    'trading_hours': {
        'start': '00:00',
        'end': '23:59'
    }
}

# Risk management configuration
RISK_CONFIG = {
    'max_daily_loss': -5.0,
    'position_sizing': 0.2,
    'max_drawdown': 20,
    'min_volume': 100
}