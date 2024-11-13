import os
import sys
import time
import logging
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any

from realtime_data import RealTimeData
from crypto_api import CryptoComAPI
from strategy import generate_trading_signals
from plot import plot_results
from performance_tracker import PerformanceTracker
from monitor import TradingMonitor
from live_trader import LiveTrader

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger('TradingLogger')
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler('trading_log.txt', encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def clear_console():
    """Clear the console output."""
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For macOS and Linux
    else:
        os.system('clear')

def display_data(data: pd.DataFrame) -> str:
    """Display real-time trading data and signals with detailed analysis"""
    try:
        if data.empty or len(data) < 2:
            logger.error("Insufficient data to calculate indicators")
            return "HOLD"
        
        # Clear the console before displaying new data
        clear_console()
        
        latest = data.iloc[-1]
        ma_diff = latest['SMA_short'] - latest['SMA_long']
        ma_diff_prev = data.iloc[-2]['SMA_short'] - data.iloc[-2]['SMA_long']
        
        # Display current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n================= Current Time: {current_time} =================")
        
        # Determine MA Cross signal
        ma_signal = "HOLD"
        if ma_diff > 0 and ma_diff_prev <= 0:
            ma_signal = "STRONG_BUY"
        elif ma_diff < 0 and ma_diff_prev >= 0:
            ma_signal = "STRONG_SELL"
        elif ma_diff > 0:
            ma_signal = "BUY"
        else:
            ma_signal = "SELL"
        
        # Initialize signals
        signals = []
        signals.append(("MA Cross", ma_signal))
        
        # Additional indicators
        macd_signal = "HOLD"
        if latest['MACD'] > latest['Signal_Line']:
            macd_signal = "BUY"
        elif latest['MACD'] < latest['Signal_Line']:
            macd_signal = "SELL"
        
        rsi_signal = "HOLD"
        if latest['RSI'] > 70:
            rsi_signal = "SELL"
        elif latest['RSI'] < 30:
            rsi_signal = "BUY"
        
        signals.append(("MACD", macd_signal))
        signals.append(("RSI", rsi_signal))
        
        # Display market data
        print("\n================= Market Data =================")
        print(f"Current Price: {latest['close']:.5f}")
        print(f"Open Price:    {latest['open']:.5f}")
        print(f"High Price:    {latest['high']:.5f}")
        print(f"Low Price:     {latest['low']:.5f}")
        print(f"Volume:        {latest['volume']:.2f}")
        
        # Display moving averages
        print("\n============= Moving Averages =============")
        print(f"Short MA (20): {latest['SMA_short']:.5f}")
        print(f"Long MA (50):  {latest['SMA_long']:.5f}")
        
        # Display MACD and RSI
        print("\n============= MACD and RSI =============")
        print(f"MACD:          {latest['MACD']:.5f}")
        print(f"Signal Line:   {latest['Signal_Line']:.5f}")
        print(f"RSI:           {latest['RSI']:.2f}")
        
        # Display trading signals
        print("\n============= Trading Signals =============")
        for signal_name, signal_value in signals:
            print(f"{signal_name}: {signal_value}")
        
        # Determine overall recommendation
        buy_signals = sum(1 for _, signal in signals if signal in ["BUY", "STRONG_BUY"])
        sell_signals = sum(1 for _, signal in signals if signal in ["SELL", "STRONG_SELL"])
        
        if buy_signals > sell_signals:
            recommendation = "BUY"
        elif sell_signals > buy_signals:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"
        
        print("\n============= Overall Recommendation =============")
        print(f"Recommendation: {recommendation}")
        
        return recommendation
    except Exception as e:
        logger.error(f"Error generating trading signals: {str(e)}")
        return "HOLD"

def main():
    try:
        # Initialize components
        rt_data = RealTimeData(symbol='DOGE-USD')
        live_trader = LiveTrader(
            api_key=os.getenv('API_KEY'),
            api_secret=os.getenv('API_SECRET')
        )
        
        logger.info("Starting 10 AM trading strategy...")
        
        while True:
            data = rt_data.data
            if not data.empty:
                latest = data.iloc[-1]
                
                # Execute 10 AM strategy
                result = live_trader.execute_10am_strategy(latest['close'])
                
                if result['status'] == 'success':
                    logger.info(f"Orders placed successfully: {result['orders']}")
                elif result['status'] == 'error':
                    logger.error(f"Strategy error: {result['reason']}")
                
                # Display market data
                display_data(data)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("User interrupted the program")
    finally:
        if rt_data:
            rt_data.stop()
        logger.info("Trading session ended")

if __name__ == "__main__":
    main()