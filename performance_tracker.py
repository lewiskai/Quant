import pandas as pd
from datetime import datetime

class PerformanceTracker:
    def __init__(self):
        self.trades = []
        self.current_balance = 0
        self.initial_balance = 0
    
    def add_trade(self, entry_price, exit_price, entry_time, exit_time, position_size):
        profit_loss = (exit_price - entry_price) * position_size
        self.trades.append({
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position_size': position_size,
            'profit_loss': profit_loss,
            'return_percent': (exit_price/entry_price - 1) * 100
        })
    
    def get_statistics(self):
        if not self.trades:
            return "No trades recorded"
            
        df = pd.DataFrame(self.trades)
        return {
            'Total Trades': len(df),
            'Profitable Trades': len(df[df.profit_loss > 0]),
            'Loss Trades': len(df[df.profit_loss < 0]),
            'Win Rate': len(df[df.profit_loss > 0]) / len(df) * 100,
            'Average Return': df.return_percent.mean(),
            'Max Profit': df.return_percent.max(),
            'Max Loss': df.return_percent.min(),
            'Total Profit': df.profit_loss.sum()
        } 