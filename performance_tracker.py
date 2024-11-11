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
            return "没有交易记录"
            
        df = pd.DataFrame(self.trades)
        return {
            '总交易次数': len(df),
            '盈利交易': len(df[df.profit_loss > 0]),
            '亏损交易': len(df[df.profit_loss < 0]),
            '胜率': len(df[df.profit_loss > 0]) / len(df) * 100,
            '平均收益率': df.return_percent.mean(),
            '最大收益': df.return_percent.max(),
            '最大亏损': df.return_percent.min(),
            '总收益': df.profit_loss.sum()
        } 