import pandas as pd
import numpy as np
from datetime import datetime
from logger import setup_logger

logger = setup_logger()

class RiskManager:
    def __init__(self, stop_loss_percent, take_profit_percent, max_positions, max_drawdown_percent=20):
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        self.max_positions = max_positions
        self.max_drawdown_percent = max_drawdown_percent
        self.max_daily_loss = -5.0  # 每日最大亏损限制(%)
        self.max_position_size = 0.2  # 单个仓位最大资金比例
        self.min_volume = 100  # 最小交易量限制
        self.positions = []
        self.daily_pnl = []
        self.max_drawdown = 0
        
    def can_open_position(self, price, position_size):
        """检查是否可以开新仓位"""
        # 检查持仓数量限制
        if len(self.positions) >= self.max_positions:
            logger.info("达到最大持仓数量限制")
            return False
            
        # 检查当前回撤
        if self.check_drawdown():
            logger.info("超过最大回撤限制")
            return False
            
        # 计算波动率风险
        volatility = self.calculate_volatility()
        if volatility > 0.5:  # 50%年化波动率阈值
            logger.info(f"当前波动率过高: {volatility:.2%}")
            return False
            
        return True
        
    def add_position(self, price, size, timestamp=None):
        """添加新仓位"""
        if timestamp is None:
            timestamp = datetime.now()
        
        position = {
            'entry_price': price,
            'size': size,
            'timestamp': timestamp,
            'stop_loss': price * (1 - self.stop_loss_percent/100),
            'take_profit': price * (1 + self.take_profit_percent/100)
        }
        self.positions.append(position)
        logger.info(f"新建仓位: 价格={price}, 数量={size}")
        
    def check_positions(self, current_price):
        """检查所有持仓是否触发止盈止损"""
        closed_positions = []
        remaining_positions = []
        
        for pos in self.positions:
            # 检查止损
            if current_price <= pos['stop_loss']:
                pnl = (current_price - pos['entry_price']) * pos['size']
                self.daily_pnl.append(pnl)
                closed_positions.append({
                    'type': 'stop_loss',
                    'position': pos,
                    'exit_price': current_price,
                    'pnl': pnl
                })
                logger.info(f"触发止损: 入场价={pos['entry_price']}, 出场价={current_price}")
                continue
                
            # 检查止盈
            if current_price >= pos['take_profit']:
                pnl = (current_price - pos['entry_price']) * pos['size']
                self.daily_pnl.append(pnl)
                closed_positions.append({
                    'type': 'take_profit',
                    'position': pos,
                    'exit_price': current_price,
                    'pnl': pnl
                })
                logger.info(f"触发止盈: 入场价={pos['entry_price']}, 出场价={current_price}")
                continue
                
            remaining_positions.append(pos)
            
        self.positions = remaining_positions
        return closed_positions
        
    def calculate_volatility(self, window=20):
        """计算最近的波动率"""
        if len(self.daily_pnl) < window:
            return 0
            
        returns = pd.Series(self.daily_pnl[-window:]).pct_change()
        return returns.std() * np.sqrt(252)  # 年化波动率
        
    def check_drawdown(self):
        """检查是否超过最大回撤限制"""
        if not self.daily_pnl:
            return False
            
        cumulative = np.cumsum(self.daily_pnl)
        peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - peak) / peak * 100
        self.max_drawdown = abs(min(drawdown))
        
        return self.max_drawdown > self.max_drawdown_percent
        
    def get_risk_metrics(self):
        """获取风险指标"""
        return {
            '当前持仓数': len(self.positions),
            '最大回撤': f"{self.max_drawdown:.2f}%",
            '年化波动率': f"{self.calculate_volatility():.2f}%",
            '累计盈亏': f"{sum(self.daily_pnl):.2f}"
        }