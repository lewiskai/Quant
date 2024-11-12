# backtest.py

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from strategy import moving_average_strategy
from logger import setup_logger
import yfinance as yf

logger = setup_logger()

class Backtester:
    def __init__(self, symbol, start_date, end_date, initial_capital=10000):
        """
        初始化回测系统
        
        参数:
            symbol (str): 交易对符号
            start_date (str): 开始日期 'YYYY-MM-DD'
            end_date (str): 结束日期 'YYYY-MM-DD'
            initial_capital (float): 初始资金
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = []
        self.trades = []
        self.daily_returns = []
        
        # 加载数据
        self._load_data()
        
    def _load_data(self):
        """加载历史数据"""
        try:
            logger.info(f"正在加载 {self.symbol} 的历史数据...")
            data = yf.download(self.symbol, start=self.start_date, end=self.end_date)
            
            # 确保数据格式正确
            data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
            data.columns = pd.MultiIndex.from_product([data.columns, [self.symbol]])
            
            # 应用策略
            self.data = moving_average_strategy(data, short_window=20, long_window=50)
            logger.info(f"成功加载并处理 {len(self.data)} 条数据记录")
            
        except Exception as e:
            logger.error(f"加载数据时出错: {str(e)}")
            raise
            
    def run(self):
        """运行回测"""
        logger.info("开始回测...")
        
        for i in range(1, len(self.data)):
            current_row = self.data.iloc[i]
            previous_row = self.data.iloc[i-1]
            
            # 更新持仓收益
            self._update_positions(current_row)
            
            # 检查信号
            signal = current_row[('Signal', '')]
            
            if signal == 1 and not self.positions:  # 买入信号且无持仓
                self._open_long_position(current_row)
            elif signal == -1 and self.positions:  # 卖出信号且有持仓
                self._close_positions(current_row)
                
            # 记录每日收益
            self._record_daily_return(current_row)
            
        logger.info("回测完成")
        return self._generate_results()
        
    def _update_positions(self, current_row):
        """更新持仓状态"""
        for pos in self.positions:
            pos['current_price'] = current_row[('Close', self.symbol)]
            pos['unrealized_pnl'] = (pos['current_price'] - pos['entry_price']) * pos['size']
            
    def _open_long_position(self, row):
        """开立多头仓位"""
        price = row[('Close', self.symbol)]
        position_size = self.current_capital * 0.95 / price  # 使用95%资金开仓
        
        position = {
            'entry_price': price,
            'size': position_size,
            'entry_time': row.name,
            'current_price': price,
            'unrealized_pnl': 0
        }
        
        self.positions.append(position)
        logger.info(f"开仓: 价格={price:.4f}, 数量={position_size:.4f}")
        
    def _close_positions(self, row):
        """平掉所有持仓"""
        exit_price = row[('Close', self.symbol)]
        
        for pos in self.positions:
            pnl = (exit_price - pos['entry_price']) * pos['size']
            self.current_capital += pnl
            
            self.trades.append({
                'entry_time': pos['entry_time'],
                'exit_time': row.name,
                'entry_price': pos['entry_price'],
                'exit_price': exit_price,
                'size': pos['size'],
                'pnl': pnl,
                'return': (exit_price/pos['entry_price'] - 1) * 100
            })
            
            logger.info(f"平仓: 价格={exit_price:.4f}, 收益={pnl:.2f}")
            
        self.positions = []
        
    def _record_daily_return(self, row):
        """记录每日收益"""
        total_value = self.current_capital
        for pos in self.positions:
            total_value += pos['unrealized_pnl']
            
        self.daily_returns.append({
            'date': row.name,
            'total_value': total_value,
            'return': (total_value/self.initial_capital - 1) * 100
        })
        
    def _generate_results(self):
        """生成回测结果报告"""
        trades_df = pd.DataFrame(self.trades)
        daily_returns_df = pd.DataFrame(self.daily_returns)
        
        # 计算关键指标
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        
        if total_trades > 0:
            win_rate = winning_trades / total_trades * 100
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        else:
            win_rate = avg_win = avg_loss = profit_factor = 0
            
        # 计算回撤
        daily_returns_df['drawdown'] = (daily_returns_df['total_value'].cummax() - daily_returns_df['total_value']) / daily_returns_df['total_value'].cummax() * 100
        max_drawdown = daily_returns_df['drawdown'].max()
        
        # 计算夏普比率
        returns = pd.Series(daily_returns_df['return'].pct_change().dropna())
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 0 else 0
        
        results = {
            '初始资金': self.initial_capital,
            '最终资金': self.current_capital,
            '总收益率': (self.current_capital/self.initial_capital - 1) * 100,
            '年化收益率': ((self.current_capital/self.initial_capital) ** (252/len(self.data)) - 1) * 100,
            '最大回撤': max_drawdown,
            '夏普比率': sharpe_ratio,
            '总交易次数': total_trades,
            '胜率': win_rate,
            '平均盈利': avg_win,
            '平均亏损': avg_loss,
            '盈亏比': profit_factor,
            '交易记录': trades_df,
            '每日收益': daily_returns_df
        }
        
        self._plot_results(daily_returns_df)
        return results
        
    def _plot_results(self, daily_returns_df):
        """绘制回测结果图表"""
        plt.figure(figsize=(15, 10))
        
        # 设置样式
        plt.style.use('seaborn')
        
        # 创建子图
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
        
        # 绘制资金曲线
        ax1.plot(daily_returns_df['date'], daily_returns_df['total_value'])
        ax1.set_title('资金曲线')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('资金')
        ax1.grid(True)
        
        # 绘制回撤
        ax2.fill_between(daily_returns_df['date'], daily_returns_df['drawdown'], 0, alpha=0.3, color='red')
        ax2.set_title('回撤')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('回撤 (%)')
        ax2.grid(True)
        
        # 绘制收益分布
        if len(self.trades) > 0:
            returns = pd.DataFrame(self.trades)['return']
            sns.histplot(returns, kde=True, ax=ax3)
            ax3.set_title('收益分布')
            ax3.set_xlabel('收益率 (%)')
            ax3.set_ylabel('频率')
            
        plt.tight_layout()
        plt.show()

def main():
    # 运行回测
    backtester = Backtester(
        symbol="DOGE-USD",
        start_date="2023-01-01",
        end_date="2024-11-11",
        initial_capital=10000
    )
    
    results = backtester.run()
    
    # 打印回测结果
    print("\n=== 回测结果 ===")
    print(f"初始资金: ${results['初始资金']:,.2f}")
    print(f"最终资金: ${results['最终资金']:,.2f}")
    print(f"总收益率: {results['总收益率']:.2f}%")
    print(f"年化收益率: {results['年化收益率']:.2f}%")
    print(f"最大回撤: {results['最大回撤']:.2f}%")
    print(f"夏普比率: {results['夏普比率']:.2f}")
    print(f"\n交易统计:")
    print(f"总交易次数: {results['总交易次数']}")
    print(f"胜率: {results['胜率']:.2f}%")
    print(f"平均盈利: ${results['平均盈利']:,.2f}")
    print(f"平均亏损: ${results['平均亏损']:,.2f}")
    print(f"盈亏比: {results['盈亏比']:.2f}")

if __name__ == "__main__":
    main()