# backtest.py

import pandas as pd
import numpy as np
from risk_manager import RiskManager
from logger import setup_logger

logger = setup_logger()

class BackTester:
    def __init__(self, data, risk_manager, initial_capital=10000):
        self.data = data
        self.risk_manager = risk_manager
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = []
        self.trades = []
        
    def run(self):
        """运行回测"""
        for index, row in self.data.iterrows():
            # 检查现有持仓
            closed_positions = self.risk_manager.check_positions(row['Close'])
            for pos in closed_positions:
                self.process_closed_position(pos, index)
            
            # 检查是否开新仓
            signal = row['Signal']
            if signal != 0 and self.risk_manager.can_open_position(row['Close'], self.calculate_position_size()):
                self.open_position(row['Close'], signal, index)
                
        # 计算回测结果
        return self.calculate_results()
        
    def calculate_position_size(self):
        """计算仓位大小"""
        return self.current_capital * 0.1  # 使用10%资金开仓
        
    def process_closed_position(self, closed_pos, timestamp):
        """处理已平仓位"""
        self.current_capital += closed_pos['pnl']
        self.trades.append({
            'entry_time': closed_pos['position']['timestamp'],
            'exit_time': timestamp,
            'entry_price': closed_pos['position']['entry_price'],
            'exit_price': closed_pos['exit_price'],
            'pnl': closed_pos['pnl'],
            'type': closed_pos['type']
        })
        
    def open_position(self, price, signal, timestamp):
        """开新仓位"""
        size = self.calculate_position_size()
        self.risk_manager.add_position(price, size, timestamp)
        logger.info(f"开仓: 价格={price}, 数量={size}, 信号={signal}")
        
    def calculate_results(self):
        """计算回测结果"""
        trades_df = pd.DataFrame(self.trades)
        
        results = {
            '初始资金': self.initial_capital,
            '最终资金': self.current_capital,
            '总收益率': (self.current_capital / self.initial_capital - 1) * 100,
            '交易次数': len(self.trades),
            '胜率': len(trades_df[trades_df['pnl'] > 0]) / len(trades_df) if len(trades_df) > 0 else 0,
            '平均收益': trades_df['pnl'].mean() if len(trades_df) > 0 else 0,
            '最大回撤': self.risk_manager.max_drawdown,
            '夏普比率': self.calculate_sharpe_ratio(trades_df)
        }
        
        return results
        
    def calculate_sharpe_ratio(self, trades_df, risk_free_rate=0.02):
        """计算夏普比率"""
        if len(trades_df) == 0:
            return 0
            
        returns = trades_df['pnl'].pct_change()
        excess_returns = returns - risk_free_rate/252
        if excess_returns.std() == 0:
            return 0
            
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()