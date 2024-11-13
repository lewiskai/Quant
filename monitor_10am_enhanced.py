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
import pandas as pd
from scipy import stats

class EnhancedTenAMTrader:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://deriv-api.crypto.com/v1"
        
        # Enhanced price alerts with more levels
        self.price_alerts = {
            'level1': 0.399500,  # Conservative
            'level1_5': 0.399200,  # Intermediate 1
            'level2': 0.398800,   # Moderate
            'level2_5': 0.398500,  # Intermediate 2
            'level3': 0.398200    # Aggressive
        }
        
        # Enhanced volume tracking
        self.volume_thresholds = {
            'large_trade': 200,    # Large trade definition
            'volume_spike': 2.0,   # Multiple of average volume
            'min_volume': 1000000  # Minimum daily volume
        }
        
        # Technical indicators
        self.vwap_5min = deque(maxlen=300)  # 5-minute VWAP
        self.momentum_data = deque(maxlen=20)  # Momentum calculation
        self.order_book_history = deque(maxlen=100)  # Order book imbalance
        
        self.monitoring = False
        self.orders = []
        self.trailing_stops = {}  # Track trailing stops for each order

    def calculate_technical_indicators(self, price: float, volume: float):
        """Calculate enhanced technical indicators"""
        self.vwap_5min.append((price, volume))
        self.momentum_data.append(price)
        
        vwap = sum(p*v for p,v in self.vwap_5min) / sum(v for _,v in self.vwap_5min)
        momentum = (price / list(self.momentum_data)[0] - 1) if len(self.momentum_data) > 1 else 0
        
        return {
            'vwap': vwap,
            'momentum': momentum,
            'price_velocity': self.calculate_price_velocity(),
            'volume_profile': self.analyze_volume_profile()
        }

    def create_dynamic_orders(self, total_quantity: float = 100):
        """Create orders with dynamic sizing based on volume"""
        last, volume, bid, ask = self.get_market_details()
        book_analysis = self.analyze_order_book()
        
        # Adjust quantities based on volume profile
        base_layers = [
            (0.399200, 0.30),
            (0.398600, 0.40),
            (0.398200, 0.30)
        ]
        
        # Adjust based on order book imbalance
        adjusted_layers = self.adjust_orders_by_imbalance(base_layers, book_analysis)
        
        orders = []
        for price, ratio in adjusted_layers:
            quantity = total_quantity * ratio
            
            # Create primary order
            order = self.create_order(
                side="BUY",
                price=f"{price:.6f}",
                quantity=f"{quantity:.2f}"
            )
            
            if order.get('code') == 0:
                order_id = order['result']['order_id']
                orders.append(order_id)
                
                # Set trailing stop
                self.trailing_stops[order_id] = {
                    'highest_price': price,
                    'stop_percent': 0.15
                }
                
                print(f"Created order at {price}: {quantity} DOGE with 0.15% trailing stop")
        
        return orders

    def monitor_with_enhanced_alerts(self):
        """Enhanced monitoring with all indicators"""
        while self.monitoring:
            try:
                # Get market data
                last, volume, bid, ask = self.get_market_details()
                book = self.get_market_depth(depth=10)
                indicators = self.calculate_technical_indicators(last, volume)
                
                # Current time
                current_time = datetime.now().strftime("%H:%M:%S")
                
                # Print enhanced dashboard
                self.print_enhanced_dashboard(
                    current_time, last, volume, bid, ask,
                    book, indicators
                )
                
                # Check all conditions
                self.check_conditions(last, volume, indicators)
                
                # Update trailing stops
                self.update_trailing_stops(last)
                
            except Exception as e:
                print(f"Error in monitoring: {str(e)}")
            
            time.sleep(5)

    def print_enhanced_dashboard(self, time, last, volume, bid, ask, book, indicators):
        """Print comprehensive market dashboard"""
        print("\n" + "="*80)
        print(f"Time: {time}")
        print(f"Price: {last:.6f} | Bid/Ask: {bid:.6f}/{ask:.6f}")
        print(f"VWAP (5min): {indicators['vwap']:.6f}")
        print(f"Momentum: {indicators['momentum']*100:+.2f}%")
        print(f"Volume Profile: {indicators['volume_profile']}")
        print("\nOrder Book Imbalance:")
        self.print_order_book_analysis(book)
        print("\nPrice Targets:")
        for level, price in self.price_alerts.items():
            diff = (price - last)/last * 100
            print(f"{level}: {price:.6f} ({diff:+.2f}%)")
        print("="*80)

    def check_conditions(self, price, volume, indicators):
        """Check all trading conditions"""
        # Price alerts
        for level, target in self.price_alerts.items():
            if price <= target:
                self.alert(f"Price reached {level}: {target}")
        
        # Volume conditions
        if volume > self.volume_thresholds['large_trade']:
            self.alert(f"Large volume detected: {volume}")
        
        # Technical conditions
        if indicators['momentum'] < -0.002:  # -0.2%
            self.alert("Negative momentum detected")
        
        # Order book imbalance
        if indicators['volume_profile'].get('imbalance', 0) > 1.5:
            self.alert("Significant order book imbalance")

    def update_trailing_stops(self, current_price):
        """Update trailing stops for all active orders"""
        for order_id, stop_data in self.trailing_stops.items():
            if current_price > stop_data['highest_price']:
                stop_data['highest_price'] = current_price
                new_stop = current_price * (1 - stop_data['stop_percent']/100)
                
                # Update order
                self.update_order(order_id, f"{new_stop:.6f}")
                print(f"Updated trailing stop for order {order_id} to {new_stop:.6f}")

def main():
    load_dotenv()
    trader = EnhancedTenAMTrader(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    
    print("Enhanced 10 AM Trading System Starting...")
    print("Monitoring will begin at 9:45 AM")
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=trader.monitor_with_enhanced_alerts)
    monitor_thread.start()
    
    try:
        while True:
            current_time = datetime.now()
            
            # Create orders at 10:00 AM
            if current_time.hour == 10 and current_time.minute == 0:
                trader.create_dynamic_orders()
            
            # Stop at 10:30 AM
            if current_time.hour == 10 and current_time.minute == 30:
                trader.monitoring = False
                break
            
            time.sleep(30)
    
    except KeyboardInterrupt:
        trader.monitoring = False
    
    monitor_thread.join()
    print("Trading session completed")

if __name__ == "__main__":
    main() 