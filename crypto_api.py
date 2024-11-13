import requests
import hmac
import hashlib
import json
import time
import logging
import websocket
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CryptoComAPI:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.crypto.com/v2"
        self.ws_url = "wss://stream.crypto.com/v2/market"
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        })
        
        # Test connection
        self.test_connection()

    def test_connection(self) -> None:
        """Test API connection"""
        try:
            response = self._send_private_request(
                method="private/get-account-summary",
                params={}
            )
            
            if response.get('code') == 0:
                logger.info("API connection successful")
                logger.info(f"Account info: {response['result']}")
            else:
                raise ConnectionError(f"API connection failed: {response}")
                
        except Exception as e:
            logger.error(f"API connection test failed: {str(e)}")
            raise

    def _send_private_request(self, method: str, params: Dict = {}) -> Dict:
        """Send private API request"""
        try:
            nonce = int(time.time() * 1000)
            request_body = {
                "id": nonce,
                "method": method,
                "api_key": self.api_key,
                "params": params,
                "nonce": nonce
            }
            
            # Generate signature
            param_str = ''.join(f'{key}{params[key]}' for key in sorted(params.keys()))
            sig_payload = f"{method}{param_str}{nonce}"
            request_body["sig"] = hmac.new(
                bytes(self.api_secret, 'utf-8'),
                msg=bytes(sig_payload, 'utf-8'),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            response = self.session.post(
                f"{self.base_url}/{method}",
                json=request_body
            )
            return response.json()
            
        except Exception as e:
            logger.error(f"Error sending request: {str(e)}")
            raise

    def get_market_price(self, symbol: str = "DOGE_USDT") -> float:
        """Get current market price"""
        try:
            ws = websocket.create_connection(self.ws_url)
            
            subscribe_message = {
                "id": 1,
                "method": "subscribe",
                "params": {
                    "channels": [f"ticker.{symbol}"]
                }
            }
            
            ws.send(json.dumps(subscribe_message))
            response = json.loads(ws.recv())
            
            if 'result' in response and 'data' in response['result']:
                price = float(response['result']['data'][0]['k'])
                ws.close()
                return price
            
            ws.close()
            raise ValueError("Unable to get market price")
            
        except Exception as e:
            logger.error(f"Error getting market price: {str(e)}")
            raise

    def create_order(self, side: str, price: str, quantity: str) -> Dict:
        """Create new order"""
        try:
            params = {
                "instrument_name": "DOGEUSDT",
                "side": side,
                "type": "LIMIT",
                "price": price,
                "quantity": quantity,
                "time_in_force": "GOOD_TILL_CANCEL",
                "exec_inst": "POST_ONLY"
            }
            
            response = self._send_private_request("private/create-order", params)
            
            if response.get('code') == 0:
                order_id = response['result']['order_id']
                time.sleep(1)
                
                open_orders = self._send_private_request(
                    method="private/get-open-orders",
                    params={"instrument_name": "DOGEUSDT"}
                )
                
                if open_orders.get('code') == 0:
                    order_list = open_orders['result'].get('order_list', [])
                    if any(order['order_id'] == order_id for order in order_list):
                        return response
                    else:
                        raise ValueError("Order not found in open orders list")
            
            raise ValueError(f"Order creation failed: {response}")
            
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise

    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order"""
        try:
            params = {
                "instrument_name": "DOGE_USDT",
                "order_id": order_id
            }
            
            return self._send_private_request("private/cancel-order", params)
            
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            raise

    def get_order_status(self, order_id: str) -> Dict:
        """Get order status"""
        try:
            params = {
                "instrument_name": "DOGE_USDT",
                "order_id": order_id
            }
            
            return self._send_private_request("private/get-order-detail", params)
            
        except Exception as e:
            logger.error(f"Error getting order status: {str(e)}")
            raise
