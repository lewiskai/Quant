# trading.py

import requests
import time
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
BASE_URL = 'https://api.binance.com'

class AutoTrader:
    def __init__(self, api_key, api_secret, risk_manager):
        self.api_key = api_key
        self.api_secret = api_secret
        self.risk_manager = risk_manager
        self.monitor = TradingMonitor()
        
    async def start_trading(self):
        """启动自动交易"""
        while True:
            try:
                # 获取市场数据
                market_data = await self.get_market_data()
                
                # 更新监控指标
                self.monitor.update_metrics(
                    market_data['price'],
                    self.positions,
                    self.balance
                )
                
                # 检查是否需要交易
                if self.should_trade(market_data):
                    await self.execute_trade(market_data)
                    
                # 检查持仓管理
                await self.manage_positions()
                
            except Exception as e:
                logger.error(f"交易执行错误: {str(e)}")
                await asyncio.sleep(5)

def place_buy_order(symbol, quantity):
    endpoint = '/api/v3/order'
    params = {
        'symbol': symbol,
        'side': 'BUY',
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': int(time.time() * 1000),
    }
    headers = {
        'X-MBX-APIKEY': API_KEY,
    }
    # Add HMAC-SHA256 signature (required for secure requests)
    params['signature'] = sign_request(params, SECRET_KEY)
    
    response = requests.post(BASE_URL + endpoint, headers=headers, params=params)
    return response.json()

def place_sell_order(symbol, quantity):
    endpoint = '/api/v3/order'
    params = {
        'symbol': symbol,
        'side': 'SELL',
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': int(time.time() * 1000),
    }
    headers = {
        'X-MBX-APIKEY': API_KEY,
    }
    params['signature'] = sign_request(params, SECRET_KEY)
    
    response = requests.post(BASE_URL + endpoint, headers=headers, params=params)
    return response.json()

def sign_request(params, secret):
    # Create a signature with HMAC-SHA256 (specific to Binance)
    import hmac
    import hashlib
    query_string = '&'.join(["{}={}".format(d, params[d]) for d in params])
    return hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()