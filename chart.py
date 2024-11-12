import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LiveChart:
    def __init__(self, title="DOGE-USD Live Trading Chart"):
        """Initialize the live trading chart"""
        self.title = title
        self.fig, self.axes = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
        self.fig.suptitle(title, fontsize=12)
        
        # Main price chart
        self.ax1 = self.axes[0]
        self.ax1.set_title('Price and Moving Averages')
        self.ax1.set_ylabel('Price (USDT)')
        
        # Volume chart
        self.ax2 = self.axes[1]
        self.ax2.set_title('Volume')
        self.ax2.set_ylabel('Volume')
        
        # Initialize empty lines
        self.price_line, = self.ax1.plot([], [], label='Price', color='black')
        self.ma20_line, = self.ax1.plot([], [], label='MA20', color='blue')
        self.ma50_line, = self.ax1.plot([], [], label='MA50', color='red')
        self.volume_bars = self.ax2.bar([], [], color='gray', alpha=0.5)
        
        # Store trade points
        self.buy_points = {'times': [], 'prices': []}
        self.sell_points = {'times': [], 'prices': []}
        
        # Add legend
        self.ax1.legend()
        plt.tight_layout()

    def update_chart(self, data: pd.DataFrame, trade_history: list):
        """Update the chart with new data"""
        try:
            if data.empty:
                logger.warning("Empty data received")
                return
                
            # Clear previous data
            self.ax1.clear()
            self.ax2.clear()
            
            # Keep only the last 100 data points
            data = data.tail(100).copy()
            
            # Get column names (with more robust checking)
            close_col = 'close'
            volume_col = 'volume'  # Changed from 'Volume' to 'volume'
            
            # Find MA columns more robustly
            ma_cols = [col for col in data.columns if isinstance(col, tuple)]
            ma20_col = next((col for col in ma_cols if 'Short_MA' in col[0] or 'MA20' in col[0]), None)
            ma50_col = next((col for col in ma_cols if 'Long_MA' in col[0] or 'MA50' in col[0]), None)
            
            # Plot price
            self.ax1.plot(data.index, data[close_col], label='Price', color='black')
            
            # Plot MAs if available
            if ma20_col:
                self.ax1.plot(data.index, data[ma20_col], label='MA20', color='blue')
            if ma50_col:
                self.ax1.plot(data.index, data[ma50_col], label='MA50', color='red')
            
            # Plot volume if available
            if volume_col in data.columns:
                self.ax2.bar(data.index, data[volume_col], color='gray', alpha=0.5)
            
            # Plot stored trade points
            if self.buy_points['times'] and self.buy_points['prices']:
                # Filter only points within the current view
                mask = [t in data.index for t in self.buy_points['times']]
                if any(mask):
                    times = [t for t, m in zip(self.buy_points['times'], mask) if m]
                    prices = [p for p, m in zip(self.buy_points['prices'], mask) if m]
                    self.ax1.scatter(times, prices, color='green', marker='^', s=100, label='Buy')
            
            if self.sell_points['times'] and self.sell_points['prices']:
                # Filter only points within the current view
                mask = [t in data.index for t in self.sell_points['times']]
                if any(mask):
                    times = [t for t, m in zip(self.sell_points['times'], mask) if m]
                    prices = [p for p, m in zip(self.sell_points['prices'], mask) if m]
                    self.ax1.scatter(times, prices, color='red', marker='v', s=100, label='Sell')
            
            # Format axes
            self.ax1.set_title('Price and Moving Averages')
            self.ax1.set_ylabel('Price (USDT)')
            self.ax1.legend()
            self.ax1.grid(True)
            
            self.ax2.set_title('Volume')
            self.ax2.set_ylabel('Volume')
            self.ax2.grid(True)
            
            # Rotate x-axis labels
            plt.setp(self.ax1.get_xticklabels(), rotation=45)
            plt.setp(self.ax2.get_xticklabels(), rotation=45)
            
            # Update layout
            plt.tight_layout()
            
            # Draw the update
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            
        except Exception as e:
            logger.error(f"Error updating chart: {str(e)}")
            logger.debug("Error details:", exc_info=True)
    
    def add_trade_marker(self, time, price, trade_type):
        """Add a trade marker to the chart"""
        if trade_type == 'BUY':
            self.buy_points['times'].append(time)
            self.buy_points['prices'].append(price)
        else:
            self.sell_points['times'].append(time)
            self.sell_points['prices'].append(price)
    
    def show(self):
        """Display the chart"""
        plt.show(block=False)
    
    def close(self):
        """Close the chart"""
        plt.close(self.fig)