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
import winsound  # For Windows alerts

class TenAMTrader:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://deriv-api.crypto.com/v1"
        self.price_alerts = {
            'level1': 0.399500,
            'level2': 0.398800,
            'level3': 0.398200
        }
        self.volume_threshold = 1000000  # 1M DOGE volume trigger
        self.orders = []
        self.monitoring = False

    def create_layered_orders(self, total_quantity: float = 100):
        """Create layered buy orders"""
        layers = [
            (0.399200, 0.30),  # 30% of quantity
            (0.398600, 0.40),  # 40% of quantity
            (0.398200, 0.30)   # 30% of quantity
        ]
        
        orders = []
        for price, ratio in layers:
            quantity = total_quantity * ratio
            order = self.create_order(
                side="BUY",
                price=f"{price:.6f}",
                quantity=f"{quantity:.2f}"
            )
            if order.get('code') == 0:
                orders.append(order['result']['order_id'])
                print(f"Created order at {price}: {quantity} DOGE")
        
        return orders

    def monitor_volume_profile(self):
        """Monitor real-time volume profile"""
        while self.monitoring:
            try:
                trades = self.get_trade_flow_analysis()
                volume_1min = sum(float(t['q']) for t in trades['recent_trades'])
                
                print(f"\nVolume Profile ({datetime.now().strftime('%H:%M:%S')})")
                print(f"1min Volume: {volume_1min:.2f}")
                print(f"Buy Pressure: {trades['buy_pressure']*100:.1f}%")
                
                if volume_1min > self.volume_threshold/60:  # Scaled to per minute
                    self.alert("High volume detected!")
            
            except Exception as e:
                print(f"Error in volume monitoring: {str(e)}")
            
            time.sleep(60)  # Update every minute

    def monitor_price_levels(self):
        """Monitor price levels and alerts"""
        while self.monitoring:
            try:
                last, volume, bid, ask = self.get_market_details()
                
                print(f"\nPrice Monitor ({datetime.now().strftime('%H:%M:%S')})")
                print(f"Current: {last:.6f}")
                print(f"Targets: {json.dumps(self.price_alerts, indent=2)}")
                
                # Check price alerts
                for level, price in self.price_alerts.items():
                    if last <= price:
                        self.alert(f"Price reached {level}: {price}")
                
            except Exception as e:
                print(f"Error in price monitoring: {str(e)}")
            
            time.sleep(5)  # Update every 5 seconds

    def start_monitoring(self):
        """Start all monitoring threads"""
        self.monitoring = True
        
        # Start price monitoring
        price_thread = threading.Thread(target=self.monitor_price_levels)
        price_thread.start()
        
        # Start volume monitoring
        volume_thread = threading.Thread(target=self.monitor_volume_profile)
        volume_thread.start()
        
        print("Monitoring started...")
        return price_thread, volume_thread

    def alert(self, message: str):
        """Trigger alert with sound and message"""
        print(f"\nALERT: {message}")
        winsound.Beep(1000, 500)  # Windows beep

def main():
    load_dotenv()
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    
    trader = TenAMTrader(api_key, api_secret)
    
    # Start monitoring at 9:45 AM
    target_time = datetime.now().replace(hour=9, minute=45, second=0)
    
    print(f"Waiting for 9:45 AM to start monitoring...")
    while datetime.now() < target_time:
        time.sleep(30)
    
    # Start monitoring
    price_thread, volume_thread = trader.start_monitoring()
    
    try:
        while True:
            current_time = datetime.now()
            
            # Create orders at 10:00 AM
            if current_time.hour == 10 and current_time.minute == 0:
                print("\nCreating layered orders...")
                trader.create_layered_orders()
            
            # Stop monitoring at 10:30 AM
            if current_time.hour == 10 and current_time.minute == 30:
                trader.monitoring = False
                break
            
            time.sleep(30)
    
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        trader.monitoring = False
    
    price_thread.join()
    volume_thread.join()
    print("Monitoring stopped")

if __name__ == "__main__":
    main() 