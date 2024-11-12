import pandas as pd
import logging
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger('TradingLogger')

class PaperTrader:
    def __init__(self, initial_balance: float = 10000.0):
        """Initialize paper trading account"""
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0.0
        self.trades: List[Dict] = []
        self.current_price = 0.0
        self.last_action = "NONE"
        
    def calculate_metrics(self) -> Dict:
        """Calculate trading performance metrics"""
        total_trades = len(self.trades)
        if total_trades == 0:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_loss": 0.0,
                "return_pct": 0.0
            }
            
        winning_trades = sum(1 for trade in self.trades if trade['profit'] > 0)
        total_profit = sum(trade['profit'] for trade in self.trades)
        
        return {
            "total_trades": total_trades,
            "win_rate": (winning_trades / total_trades) * 100,
            "profit_loss": total_profit,
            "return_pct": (total_profit / self.initial_balance) * 100
        }
        
    def execute_trade(self, signal: str, price: float, timestamp: datetime) -> None:
        """Execute a paper trade based on signal"""
        logger.debug(f"Evaluating trade signal: {signal} at price {price}")
        
        if signal == self.last_action:
            logger.debug("Signal is the same as last action, no trade executed.")
            return
            
        if signal in ["STRONG BUY", "BUY"] and self.position == 0:
            # Calculate position size (use 95% of balance to account for fees)
            amount = (self.balance * 0.95) / price
            cost = amount * price
            
            self.position = amount
            self.balance -= cost
            self.last_action = signal
            
            self.trades.append({
                "type": "BUY",
                "price": price,
                "amount": amount,
                "cost": cost,
                "timestamp": timestamp,
                "profit": 0
            })
            
            logger.info(f"PAPER TRADE: BUY {amount:.4f} units at {price:.4f}")
            
        elif signal in ["STRONG SELL", "SELL"] and self.position > 0:
            # Close position
            revenue = self.position * price
            profit = revenue - self.trades[-1]["cost"]
            self.balance += revenue
            
            self.trades[-1]["exit_price"] = price
            self.trades[-1]["exit_time"] = timestamp
            self.trades[-1]["profit"] = profit
            
            logger.info(f"PAPER TRADE: SELL {self.position:.4f} units at {price:.4f}")
            logger.info(f"PAPER TRADE: Profit/Loss: {profit:.2f} USDT")
            
            self.position = 0
            self.last_action = signal
            
    def get_position_value(self, current_price: float) -> float:
        """Calculate current position value"""
        return self.position * current_price
        
    def get_total_value(self, current_price: float) -> float:
        """Calculate total account value"""
        return self.balance + self.get_position_value(current_price) 