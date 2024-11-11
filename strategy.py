# strategy.py

import pandas as pd
import logging
import numpy as np

# 配置日志记录器
logger = logging.getLogger(__name__)

def moving_average_strategy(data: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    """
    Simple moving average crossover strategy.
    """
    try:
        # 获取收盘价列（使用更安全的方式）
        if isinstance(data.columns, pd.MultiIndex):
            close_col = ('Close', data.columns.get_level_values(1)[0])
        else:
            close_col = 'Close'
            
        close_prices = data[close_col]
        
        # 计算移动平均线
        data[('Short_MA', '')] = close_prices.rolling(window=short_window).mean()
        data[('Long_MA', '')] = close_prices.rolling(window=long_window).mean()
        
        # 计算EMA
        data[('EMA_12', '')] = close_prices.ewm(span=12).mean()
        data[('EMA_26', '')] = close_prices.ewm(span=26).mean()
        
        # 计算MACD
        data[('MACD', '')] = data[('EMA_12', '')] - data[('EMA_26', '')]
        data[('Signal_Line', '')] = data[('MACD', '')].ewm(span=9).mean()
        data[('MACD_Hist', '')] = data[('MACD', '')] - data[('Signal_Line', '')]
        
        # 计算RSI (14周期)
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data[('RSI', '')] = 100 - (100 / (1 + rs))
        
        # 计算布林带 (20周期)
        data[('BB_Middle', '')] = close_prices.rolling(window=20).mean()
        std = close_prices.rolling(window=20).std()
        data[('BB_Upper', '')] = data[('BB_Middle', '')] + (std * 2)
        data[('BB_Lower', '')] = data[('BB_Middle', '')] - (std * 2)
        
        # 计算成交量加权平均价格 (VWAP)
        if ('Volume', close_col) in data.columns:
            data[('VWAP', '')] = (close_prices * data[('Volume', close_col)]).cumsum() / data[('Volume', close_col)].cumsum()
        
        # 计算趋势强度
        data[('Trend', '')] = data[('Short_MA', '')] - data[('Long_MA', '')]
        data[('Trend_Strength', '')] = abs(data[('Trend', '')]) / data[('Long_MA', '')] * 100
        
        # 计算动量指标
        data[('Momentum', '')] = close_prices.diff(periods=10)
        
        # 添加更多技术指标
        data[('RSI_Trend', '')] = data[('RSI', '')] > data[('RSI', '')].shift(1)
        data[('Volume_Trend', '')] = data[('Volume', '')].rolling(window=5).mean()
        
        # 综合多个指标
        data[('Signal', '')] = np.where(
            (data[('MACD_Hist', '')] > 0) & 
            (data[('RSI_Trend', '')] == True) & 
            (data[('Volume_Trend', '')] > data[('Volume_Trend', '')].shift(1)),
            1, -1)
        
        # 计算价格偏离度
        data[('Price_Dev_Short', '')] = (close_prices - data[('Short_MA', '')]) / data[('Short_MA', '')] * 100
        data[('Price_Dev_Long', '')] = (close_prices - data[('Long_MA', '')]) / data[('Long_MA', '')] * 100
        
        # 添加调试日志
        logger.debug(f"短期MA: {data[('Short_MA', '')].tail()}")
        logger.debug(f"长期MA: {data[('Long_MA', '')].tail()}")
        
        return data
    except Exception as e:
        logger.error(f"策略计算出错: {str(e)}")
        return data