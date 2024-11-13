import os
from dotenv import load_dotenv
import json
import time
import hmac
import hashlib
import requests
from typing import Dict, Any, List
from datetime import datetime
import numpy as np
from collections import deque
import threading
import winsound

class LiveTrader:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://deriv-api.crypto.com/v1"
        
        # Real trading parameters
        self.total_usdt = 100  # Total USDT to use
        self.price_levels = {
            'entry1': 0.399200,  # 35% of funds
            'entry2': 0.398600,  # 35% of funds
            'entry3': 0.398200   # 30% of funds
        }
        
        # Trailing stop parameters
        self.trail_percent = 0.15
        self.active_orders = {}
        
        # Monitoring flags
        self.monitoring = False
        self.orders_placed = False

    def calculate_quantities(self):
        """Calculate DOGE quantities for each price level"""
        quantities = {
            'entry1': (self.total_usdt * 0.35) / self.price_levels['entry1'],
            'entry2': (self.total_usdt * 0.35) / self.price_levels['entry2'],
            'entry3': (self.total_usdt * 0.30) / self.price_levels['entry3']
        }
        return {k: round(v, 2) for k, v in quantities.items()}

    def place_live_orders(self):
        """Place real trading orders"""
        if self.orders_placed:
            print("Orders already placed")
            return
        
        quantities = self.calculate_quantities()
        
        try:
            for level, price in self.price_levels.items():
                order = self.create_order(
                    side="BUY",
                    price=f"{price:.6f}",
                    quantity=f"{quantities[level]:.2f}"
                )
                
                if order.get('code') == 0:
                    order_id = order['result']['order_id']
                    self.active_orders[order_id] = {
                        'price': price,
                        'quantity': quantities[level],
                        'level': level
                    }
                    print(f"Placed order at {price}: {quantities[level]} DOGE")
                else:
                    print(f"Order placement failed for {level}: {order}")
            
            self.orders_placed = True
            
        except Exception as e:
            print(f"Error placing orders: {str(e)}")

    def monitor_live_trades(self):
        """Monitor live trading positions"""
        while self.monitoring:
            try:
                last, volume, bid, ask = self.get_market_details()
                
                print(f"\n{datetime.now().strftime('%H:%M:%S')} Market Update:")
                print(f"Current Price: {last:.6f}")
                print(f"Bid/Ask: {bid:.6f}/{ask:.6f}")
                print("\nActive Orders:")
                
                for order_id, details in self.active_orders.items():
                    status = self.get_order_status(order_id)
                    if status.get('code') == 0:
                        result = status['result']
                        print(f"Level: {details['level']}")
                        print(f"Price: {details['price']:.6f}")
                        print(f"Status: {result['status']}")
                        print(f"Filled: {result.get('cumulative_quantity', '0')}")
                        print("---")
                
                # Check if we should update trailing stops
                self.update_trailing_stops(last)
                
            except Exception as e:
                print(f"Error in monitoring: {str(e)}")
            
            time.sleep(5)

    def start_live_trading(self):
        """Start live trading session"""
        print("\nStarting live trading session...")
        print("Waiting for 9:45 AM to begin monitoring")
        
        target_time = datetime.now().replace(hour=9, minute=45, second=0)
        
        while datetime.now() < target_time:
            time.sleep(30)
            print(f"Current time: {datetime.now().strftime('%H:%M:%S')}")
        
        self.monitoring = True
        monitor_thread = threading.Thread(target=self.monitor_live_trades)
        monitor_thread.start()
        
        try:
            while True:
                current_time = datetime.now()
                
                # Place orders at 10:00 AM
                if current_time.hour == 10 and current_time.minute == 0 and not self.orders_placed:
                    print("\nPlacing live orders...")
                    self.place_live_orders()
                
                # End session at 10:30 AM
                if current_time.hour == 10 and current_time.minute == 30:
                    self.monitoring = False
                    break
                
                time.sleep(30)
        
        except KeyboardInterrupt:
            print("\nStopping trading session...")
            self.monitoring = False
        
        monitor_thread.join()
        self.print_trading_summary()

    def print_trading_summary(self):
        """Print summary of trading session"""
        print("\nTrading Session Summary:")
        total_filled = 0
        total_cost = 0
        
        for order_id, details in self.active_orders.items():
            status = self.get_order_status(order_id)
            if status.get('code') == 0:
                result = status['result']
                filled = float(result.get('cumulative_quantity', '0'))
                price = float(result.get('price', '0'))
                total_filled += filled
                total_cost += filled * price
                
                print(f"\nOrder {order_id}:")
                print(f"Price: {price:.6f}")
                print(f"Filled: {filled:.2f}")
                print(f"Status: {result['status']}")
        
        if total_filled > 0:
            avg_price = total_cost / total_filled
            print(f"\nTotal DOGE bought: {total_filled:.2f}")
            print(f"Average price: {avg_price:.6f}")
            print(f"Total USDT spent: {total_cost:.2f}")

def main():
    load_dotenv()
    trader = LiveTrader(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    trader.start_live_trading()

if __name__ == "__main__":
    main() 