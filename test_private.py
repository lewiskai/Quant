import os
from dotenv import load_dotenv
import json
import time
import hmac
import hashlib
import requests
from typing import Dict, Any, Tuple, List
from datetime import datetime
import numpy as np
from collections import deque

# Load environment variables
load_dotenv()

class CryptoTrader:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://deriv-api.crypto.com/v1"
        self.trade_flow = deque(maxlen=50)  # Increased trade history
        self.vwap_prices = deque(maxlen=20)  # For VWAP calculation
    
    def _generate_signature(self, method: str, request_id: int, params: Dict = None) -> str:
        param_str = ""
        if params:
            for key in sorted(params.keys()):
                param_str += f"{key}{params[key]}"
        
        sig_str = f"{method}{request_id}{self.api_key}{param_str}{request_id}"
        return hmac.new(
            bytes(self.api_secret, 'utf-8'),
            sig_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_market_price(self, symbol: str = "DOGE_USDT") -> float:
        response = requests.get(
            f"{self.base_url}/public/get-candlestick",
            params={"instrument_name": symbol, "timeframe": "1m"}
        )
        data = response.json()
        if data.get('result', {}).get('data'):
            return float(data['result']['data'][0]['o'])
        raise Exception("Could not get market price")
    
    def create_limit_order(self, side: str, quantity: str, price: str, symbol: str = "DOGE_USDT") -> Dict[str, Any]:
        nonce = int(time.time() * 1000)
        method = "private/create-order"
        
        params = {
            "instrument_name": symbol,
            "side": side.upper(),
            "type": "LIMIT",
            "price": price,
            "quantity": quantity,
            "time_in_force": "GOOD_TILL_CANCEL"
        }
        
        request = {
            "id": nonce,
            "method": method,
            "api_key": self.api_key,
            "params": params,
            "nonce": nonce
        }
        
        sig_str = f"{method}{request['id']}{self.api_key}"
        for key in sorted(params.keys()):
            sig_str += f"{key}{params[key]}"
        sig_str += str(nonce)
        
        request["sig"] = hmac.new(
            bytes(self.api_secret, 'utf-8'),
            sig_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        response = requests.post(
            f"{self.base_url}/private/create-order",
            json=request,
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        nonce = int(time.time() * 1000)
        method = "private/get-order-detail"
        
        params = {"order_id": order_id}
        request = {
            "id": nonce,
            "method": method,
            "api_key": self.api_key,
            "params": params,
            "nonce": nonce
        }
        
        sig_str = f"{method}{request['id']}{self.api_key}order_id{order_id}{nonce}"
        request["sig"] = hmac.new(
            bytes(self.api_secret, 'utf-8'),
            sig_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        response = requests.post(
            f"{self.base_url}/private/get-order-detail",
            json=request,
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        nonce = int(time.time() * 1000)
        method = "private/cancel-order"
        
        params = {"order_id": order_id}
        request = {
            "id": nonce,
            "method": method,
            "api_key": self.api_key,
            "params": params,
            "nonce": nonce
        }
        
        request["sig"] = self._generate_signature(method, nonce, params)
        
        response = requests.post(
            f"{self.base_url}/private/cancel-order",
            json=request,
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
    
    def monitor_order_with_price(self, order_id: str, limit_price: float, timeout_seconds: int = 300) -> None:
        start_time = time.time()
        check_interval = 5  # seconds between checks
        
        print(f"\nMonitoring order {order_id}")
        print("Time\t\tStatus\t\tFilled/Total\tLimit Price\tMarket Price\tDiff%")
        print("-" * 90)
        
        while time.time() - start_time < timeout_seconds:
            try:
                status = self.get_order_status(order_id)
                market_price = self.get_market_price()
                
                if status.get('code') == 0:
                    result = status['result']
                    current_time = datetime.now().strftime("%H:%M:%S")
                    filled = float(result['cumulative_quantity'])
                    total = float(result['quantity'])
                    price_diff = ((market_price - limit_price) / limit_price) * 100
                    
                    print(f"{current_time}\t{result['status']}\t{filled}/{total}\t"
                          f"{limit_price:.6f}\t{market_price:.6f}\t{price_diff:+.2f}%")
                    
                    if result['status'] in ['FILLED', 'CANCELED', 'REJECTED']:
                        print(f"\nOrder {result['status']}")
                        return result
                
            except Exception as e:
                print(f"Error checking status: {str(e)}")
            
            time.sleep(check_interval)
        
        print("\nMonitoring timeout reached")
        return None
    
    def update_order(self, order_id: str, new_price: str) -> Dict[str, Any]:
        """Update order with new price"""
        nonce = int(time.time() * 1000)
        method = "private/cancel-replace-order"
        
        params = {
            "order_id": order_id,
            "type": "LIMIT",
            "price": new_price
        }
        
        request = {
            "id": nonce,
            "method": method,
            "api_key": self.api_key,
            "params": params,
            "nonce": nonce
        }
        
        sig_str = f"{method}{request['id']}{self.api_key}"
        for key in sorted(params.keys()):
            sig_str += f"{key}{params[key]}"
        sig_str += str(nonce)
        
        request["sig"] = hmac.new(
            bytes(self.api_secret, 'utf-8'),
            sig_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        response = requests.post(
            f"{self.base_url}/private/cancel-replace-order",
            json=request,
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
    
    def get_market_details(self, symbol: str = "DOGE_USDT") -> Tuple[float, float, float, float]:
        """Get current market price, volume, bid and ask"""
        try:
            # Get ticker data
            ticker_response = requests.get(
                f"{self.base_url}/public/get-ticker",
                params={"instrument_name": symbol}
            )
            print(f"Raw ticker response: {ticker_response.text}")  # Debug
            
            # Get recent trades
            trades_response = requests.get(
                f"{self.base_url}/public/get-trades",
                params={"instrument_name": symbol, "count": 1}
            )
            print(f"Raw trades response: {trades_response.text}")  # Debug
            
            if ticker_response.status_code == 200:
                data = ticker_response.json()
                if data.get('result', {}).get('data'):
                    ticker = data['result']['data']
                    return (
                        float(ticker['l']),  # Last price
                        float(ticker['v']),  # 24h volume
                        float(ticker['b']),  # Best bid
                        float(ticker['k'])   # Best ask
                    )
            
            raise Exception(f"Could not get market details: {ticker_response.text}")
        except Exception as e:
            print(f"Error in get_market_details: {str(e)}")
            raise
    
    def get_market_depth(self, symbol: str = "DOGE_USDT", depth: int = 8) -> Dict[str, List]:
        """Get extended order book depth with cumulative volumes"""
        response = requests.get(
            f"{self.base_url}/public/get-book",
            params={"instrument_name": symbol, "depth": depth}
        )
        data = response.json()
        if data.get('result', {}).get('data'):
            book = data['result']['data']
            bids = [(float(bid[0]), float(bid[1])) for bid in book.get('bids', [])]
            asks = [(float(ask[0]), float(ask[1])) for ask in book.get('asks', [])]
            return {'bids': bids, 'asks': asks}
        raise Exception("Could not get market depth")
    
    def get_trade_flow(self, symbol: str = "DOGE_USDT") -> Dict[str, float]:
        """Get recent trades and calculate buy/sell pressure"""
        response = requests.get(
            f"{self.base_url}/public/get-trades",
            params={"instrument_name": symbol, "count": 50}
        )
        data = response.json()
        if data.get('result', {}).get('data'):
            trades = data['result']['data']
            buy_volume = sum(float(t['q']) for t in trades if t['s'] == 'BUY')
            sell_volume = sum(float(t['q']) for t in trades if t['s'] == 'SELL')
            total_volume = buy_volume + sell_volume
            return {
                'buy_pressure': (buy_volume / total_volume) if total_volume > 0 else 0,
                'recent_trades': trades[:5]
            }
        return {'buy_pressure': 0, 'recent_trades': []}
    
    def get_trade_flow_analysis(self, symbol: str = "DOGE_USDT") -> Dict[str, Any]:
        """Enhanced trade flow analysis"""
        response = requests.get(
            f"{self.base_url}/public/get-trades",
            params={"instrument_name": symbol, "count": 100}
        )
        data = response.json()
        if data.get('result', {}).get('data'):
            trades = data['result']['data']
            
            # Calculate various metrics
            buy_volume = sum(float(t['q']) for t in trades if t['s'] == 'BUY')
            sell_volume = sum(float(t['q']) for t in trades if t['s'] == 'SELL')
            total_volume = buy_volume + sell_volume
            
            # Calculate VWAP
            vwap = sum(float(t['p']) * float(t['q']) for t in trades) / total_volume if total_volume > 0 else 0
            
            # Calculate trade size metrics
            trade_sizes = [float(t['q']) for t in trades]
            avg_trade_size = np.mean(trade_sizes) if trade_sizes else 0
            large_trades = sum(1 for s in trade_sizes if s > avg_trade_size * 2)
            
            return {
                'buy_pressure': (buy_volume / total_volume) if total_volume > 0 else 0,
                'vwap': vwap,
                'avg_trade_size': avg_trade_size,
                'large_trades': large_trades,
                'recent_trades': trades[:5],
                'buy_volume': buy_volume,
                'sell_volume': sell_volume
            }
        return {}
    
    def monitor_with_trailing_stop(self, order_id: str, initial_price: float, 
                                 trail_percent: float = 0.12, depth: int = 10,
                                 timeout_seconds: int = 300) -> None:
        start_time = time.time()
        check_interval = 5
        highest_price = initial_price
        current_limit_price = initial_price
        price_history = []
        volume_profile = {}
        
        print(f"\nMonitoring order {order_id} with {trail_percent}% trailing stop")
        print("\nTime\t\tStatus\tBid/Ask\t\tLimit\t\tTrail%\tFlow\tVWAP\tTrend")
        print("-" * 120)
        
        while time.time() - start_time < timeout_seconds:
            try:
                status = self.get_order_status(order_id)
                last, volume, bid, ask = self.get_market_details()
                depth_data = self.get_market_depth(depth=depth)
                flow_analysis = self.get_trade_flow_analysis()
                
                price_history.append(last)
                if len(price_history) > 20:
                    price_history.pop(0)
                
                metrics = self.calculate_price_metrics(price_history)
                
                if status.get('code') == 0:
                    result = status['result']
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    # Enhanced metrics
                    trail_pct = ((ask - current_limit_price) / current_limit_price) * 100
                    spread_pct = ((ask - bid) / bid) * 100
                    buy_pressure = flow_analysis.get('buy_pressure', 0) * 100
                    vwap = flow_analysis.get('vwap', 0)
                    vwap_diff = ((last - vwap) / vwap) * 100 if vwap else 0
                    
                    # Main status line with enhanced metrics
                    print(f"{current_time}\t{result['status']}\t"
                          f"{bid:.6f}/{ask:.6f}\t"
                          f"{current_limit_price:.6f}\t"
                          f"{trail_pct:+.2f}%\t"
                          f"{buy_pressure:+.1f}%\t"
                          f"{vwap:.6f}\t"
                          f"{metrics.get('trend', 0):+.6f}")
                    
                    # Market depth and analysis
                    print("\nOrder Book Analysis:")
                    print(f"Spread: {spread_pct:.3f}% | Volatility: {metrics.get('volatility', 0):.3f}%")
                    print(f"Buy Pressure: {buy_pressure:.1f}% | VWAP Diff: {vwap_diff:+.3f}%")
                    print(f"Avg Trade Size: {flow_analysis.get('avg_trade_size', 0):.2f}")
                    print(f"Large Trades: {flow_analysis.get('large_trades', 0)}")
                    
                    print("\nOrder Book Depth (Cumulative):")
                    print("Asks:")
                    for price, size, cum_size in reversed(depth_data['asks']):
                        print(f"  {price:.6f}\t{size:.2f}\t{cum_size:.2f}")
                    
                    print("\nBids:")
                    for price, size, cum_size in depth_data['bids']:
                        print(f"  {price:.6f}\t{size:.2f}\t{cum_size:.2f}")
                    
                    print("\nRecent Trades (Price, Size, Side):")
                    for trade in flow_analysis.get('recent_trades', [])[:3]:
                        print(f"  {trade['p']}\t{trade['q']}\t{trade['s']}")
                    
                    # Execution analysis
                    est_price = self.estimate_slippage(100, depth_data, 'SELL')
                    if est_price:
                        print(f"\nEstimated execution price: {est_price:.6f}")
                        print(f"Estimated slippage: {((est_price - bid) / bid) * 100:+.3f}%")
                    
                    print("-" * 80)
                    
                    # Trailing stop logic with tighter following
                    if ask > highest_price:
                        highest_price = ask
                        new_limit_price = highest_price * (1 - trail_percent/100)
                        
                        if new_limit_price > current_limit_price:
                            current_limit_price = new_limit_price
                            new_price_str = "{:.6f}".format(new_limit_price)
                            print(f"\nPrice moved up! Updating limit price to {new_price_str}")
                            update_result = self.update_order(order_id, new_price_str)
                            if update_result.get('code') == 0:
                                print("Price update successful")
                            else:
                                print(f"Price update failed: {update_result}")
                    
                    if result['status'] in ['FILLED', 'CANCELED', 'REJECTED']:
                        print(f"\nOrder {result['status']}")
                        return result
                
            except Exception as e:
                print(f"Error checking status: {str(e)}")
            
            time.sleep(check_interval)
        
        print("\nMonitoring timeout reached")
        return None

def test_trailing_stop():
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    trader = CryptoTrader(api_key, api_secret)
    
    try:
        # Get current market details
        last, volume, bid, ask = trader.get_market_details()
        flow_analysis = trader.get_trade_flow_analysis()
        
        print(f"\nMarket Analysis:")
        print(f"Bid/Ask: {bid:.6f}/{ask:.6f}")
        print(f"Last: {last:.6f}")
        print(f"24h Volume: {volume:.0f}")
        print(f"VWAP: {flow_analysis.get('vwap', 0):.6f}")
        print(f"Buy Pressure: {flow_analysis.get('buy_pressure', 0)*100:.1f}%")
        
        # Your existing order ID
        order_id = "6530219545816105235"
        
        # Monitor with all improvements
        result = trader.monitor_with_trailing_stop(
            order_id=order_id,
            initial_price=bid,
            trail_percent=0.12,  # Even tighter trailing stop
            depth=10,  # More price levels
            timeout_seconds=300  # 5 minutes monitoring
        )
        
        if result:
            print(f"\nFinal result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"Error in trading: {str(e)}")

if __name__ == "__main__":
    test_trailing_stop() 