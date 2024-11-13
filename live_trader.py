import logging
from typing import Dict
from crypto_api import CryptoComAPI
from datetime import datetime

logger = logging.getLogger(__name__)

class LiveTrader:
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize live trader
        
        Args:
            api_key: Crypto.com API key
            api_secret: Crypto.com API secret
        """
        self.api = CryptoComAPI(api_key, api_secret)
        
        # 更新价格水平 (基于当前价格0.401650的下方)
        self.price_levels = {
            'entry1': 0.399500,  # 700 DOGE (35%)
            'entry2': 0.398800,  # 700 DOGE (35%)
            'entry3': 0.398200   # 600 DOGE (30%)
        }
        
        self.quantities = {
            'entry1': 700,  # 35%
            'entry2': 700,  # 35%
            'entry3': 600   # 30%
        }
        
        self.trail_percent = 0.15
        self.active_orders = {}
        self.orders_placed = False

    def execute_trade(self, signal: str, symbol: str, price: float) -> Dict:
        """Execute live trade based on signal"""
        try:
            # Skip if signal matches last action
            if signal == self.last_action:
                return {"status": "skipped", "reason": "Same as last action"}

            # Get account balance
            account_balance = self.api.get_account_balance()
            available_balance = float(account_balance['available_balance'])
            
            if signal in ["STRONG BUY", "BUY"] and self.current_position == 0:
                # Calculate position size based on risk percentage
                trade_amount = (available_balance * self.risk_percentage / 100)
                quantity = trade_amount / price
                
                # Execute buy order
                order = self.api.create_order(
                    symbol=symbol,
                    side="BUY",
                    type="MARKET",
                    quantity=quantity
                )
                
                self.current_position = quantity
                self.last_action = signal
                
                logger.info(f"LIVE TRADE: BUY {quantity:.4f} units at ~{price:.4f}")
                return {"status": "success", "order": order}
                
            elif signal in ["STRONG SELL", "SELL"] and self.current_position > 0:
                # Execute sell order
                order = self.api.create_order(
                    symbol=symbol,
                    side="SELL",
                    type="MARKET",
                    quantity=self.current_position
                )
                
                self.current_position = 0
                self.last_action = signal
                
                logger.info(f"LIVE TRADE: SELL {self.current_position:.4f} units at ~{price:.4f}")
                return {"status": "success", "order": order}
                
            return {"status": "skipped", "reason": "No trade conditions met"}
            
        except Exception as e:
            logger.error(f"Error executing live trade: {str(e)}")
            return {"status": "error", "reason": str(e)} 

    def execute_10am_strategy(self, current_price: float) -> Dict:
        """Execute 10 AM trading strategy"""
        try:
            if not self.orders_placed:
                logger.info("Placing initial orders now...")
                
                for level, price in self.price_levels.items():
                    order = self.api.create_order(
                        side="BUY",
                        price=f"{price:.6f}",
                        quantity=str(self.quantities[level])
                    )
                    
                    if order.get('code') == 0:
                        order_id = order['result']['order_id']
                        self.active_orders[order_id] = {
                            'price': price,
                            'quantity': self.quantities[level],
                            'level': level
                        }
                        logger.info(f"Placed order at {price}: {self.quantities[level]} DOGE")
                
                self.orders_placed = True
                return {"status": "success", "orders": self.active_orders}

            # Update trailing stops
            if self.active_orders:
                self._update_trailing_stops(current_price)

            return {"status": "monitoring", "active_orders": self.active_orders}

        except Exception as e:
            logger.error(f"Error in trading strategy: {str(e)}")
            return {"status": "error", "reason": str(e)}

    def _update_trailing_stops(self, current_price: float) -> None:
        """Update trailing stops for active orders"""
        for order_id, details in self.active_orders.items():
            status = self.api.get_order_status(order_id)
            if status.get('code') == 0:
                if status['result']['status'] == 'FILLED':
                    new_stop = current_price * (1 - self.trail_percent/100)
                    if new_stop > details['price']:
                        self.api.update_order(
                            order_id=order_id,
                            new_price=f"{new_stop:.6f}"
                        )
                        details['price'] = new_stop
                        logger.info(f"Updated stop for order {order_id} to {new_stop:.6f}") 

    def create_order(self, side: str, price: float, quantity: float) -> Dict:
        """Create new order with proper formatting"""
        try:
            params = {
                "instrument_name": "DOGE_USDT",  # 确保交易对正确
                "side": side,
                "type": "LIMIT",
                "price": f"{price:.6f}",
                "quantity": f"{quantity:.1f}",   # DOGE数量保留1位小数
                "time_in_force": "GOOD_TILL_CANCEL",  # 订单持续有效直到取消
                "exec_inst": "POST_ONLY"  # 确保订单只作为maker
            }
            
            order = self.api.create_order(**params)
            
            if order.get('code') == 0:
                order_id = order['result']['order_id']
                logger.info(f"Order placed successfully: {quantity} DOGE @ {price}")
                
                # 立即验证订单状态
                status = self.api.get_order_status(order_id)
                logger.info(f"Order status: {status}")
                
                return order
            else:
                logger.error(f"Order failed: {order}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return None 