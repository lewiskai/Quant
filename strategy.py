# strategy.py

import pandas as pd
import logging
import numpy as np
from datetime import datetime

# 配置日志记录器
logger = logging.getLogger(__name__)

def generate_trading_signals(data: pd.DataFrame) -> dict:
    """
    Generate trading signals with improved strategy focusing on stronger trends
    and reduced trading frequency
    """
    try:
        # Minimum required data points
        if len(data) < 200:
            return {'signal': 0, 'strength': 0, 'confidence': 0}

        latest = data.iloc[-1]
        
        signals = {
            'signal': 0,
            'strength': 0,
            'confidence': 0
        }

        # === Improved Risk Management ===
        min_profit_target = 0.15  # Minimum 0.15% profit target
        max_loss = 0.10          # Maximum 0.10% loss
        current_price = float(latest['close'])
        
        # === Enhanced Trend Analysis ===
        trend_period = 20
        price_trend = data['close'].tail(trend_period)
        trend_strength = abs(price_trend.iloc[-1] - price_trend.iloc[0]) / price_trend.iloc[0] * 100
        
        # === Volume Analysis ===
        volume = float(latest['volume'])
        avg_volume = float(data['volume'].rolling(20).mean().iloc[-1])
        volume_std = float(data['volume'].rolling(20).std().iloc[-1])
        significant_volume = volume > (avg_volume + volume_std)
        
        # === Market Condition Check ===
        volatility = data['close'].pct_change().tail(20).std() * 100
        is_stable_market = volatility < 0.2  # Only trade in stable conditions
        
        # === Entry Conditions ===
        if is_stable_market and significant_volume:
            if trend_strength > 0.2:  # Minimum trend strength requirement
                entry_price = current_price
                take_profit = entry_price * (1 + min_profit_target)
                stop_loss = entry_price * (1 - max_loss)
                
                signals['take_profit'] = take_profit
                signals['stop_loss'] = stop_loss
                
                # Long position
                if all([
                    latest['close'] > latest['MA_50'],
                    latest['RSI'] > 40 and latest['RSI'] < 60,
                    latest['MACD'] > latest['Signal_Line'],
                    latest['close'] > latest['BB_Middle']
                ]):
                    signals['signal'] = 1
                
                # Short position
                elif all([
                    latest['close'] < latest['MA_50'],
                    latest['RSI'] > 60 or latest['RSI'] < 40,
                    latest['MACD'] < latest['Signal_Line'],
                    latest['close'] < latest['BB_Middle']
                ]):
                    signals['signal'] = -1

        # === Position Management ===
        if hasattr(generate_trading_signals, 'last_trade'):
            time_since_trade = (datetime.now() - generate_trading_signals.last_trade).seconds
            if time_since_trade < 300:  # 5-minute minimum between trades
                signals['signal'] = 0

        if signals['signal'] != 0:
            generate_trading_signals.last_trade = datetime.now()

        return signals

    except Exception as e:
        logger.error(f"Signal generation error: {str(e)}")
        return {'signal': 0, 'strength': 0, 'confidence': 0}

def calculate_trend_stability(data: pd.DataFrame, window: int = 20) -> float:
    """Calculate how stable the trend is"""
    price_changes = data['close'].pct_change().tail(window)
    direction_changes = (price_changes > 0).diff().abs().sum()
    return 1 - (direction_changes / window)

def is_valid_entry(data: pd.DataFrame, trend_strength: float, volatility: float) -> bool:
    """Check if market conditions are suitable for entry"""
    latest = data.iloc[-1]
    
    # Check if price is near support/resistance
    bb_position = (latest['close'] - latest['BB_Lower']) / (latest['BB_Upper'] - latest['BB_Lower'])
    
    return (trend_strength > 0.5 and  # Minimum trend strength
            volatility < 2.0 and      # Maximum volatility
            0.2 < bb_position < 0.8)  # Not too close to BB extremes

def calculate_confidence(data: pd.DataFrame) -> float:
    """Calculate trade confidence based on multiple factors"""
    latest = data.iloc[-1]
    
    # Volume confidence
    volume_ratio = latest['volume'] / data['volume'].rolling(20).mean().iloc[-1]
    volume_conf = min(1.0, volume_ratio / 3)
    
    # Trend confidence
    trend_conf = abs(latest['SMA_short'] - latest['SMA_long']) / latest['SMA_long']
    
    # RSI confidence
    rsi_conf = 1.0 - abs(latest['RSI'] - 50) / 50
    
    # MACD confidence
    macd_conf = abs(latest['MACD'] - latest['Signal_Line']) / abs(latest['Signal_Line'])
    
    # Combine confidences
    total_conf = (volume_conf + trend_conf + rsi_conf + macd_conf) / 4
    return min(0.95, total_conf)  # Cap at 95% confidence

# Initialize last trade time
generate_trading_signals.last_trade = datetime.now()

def moving_average_strategy(data: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    """
    增强版移动平均策略，包含多个技术指标和信号过滤。
    """
    try:
        # 获取收盘价列
        if isinstance(data.columns, pd.MultiIndex):
            close_col = ('Close', data.columns.get_level_values(1)[0])
        else:
            close_col = 'Close'
            
        close_prices = data[close_col]
        
        # === 移动平均线 ===
        data[('Short_MA', '')] = close_prices.rolling(window=short_window).mean()
        data[('Long_MA', '')] = close_prices.rolling(window=long_window).mean()
        data[('MA_50', '')] = close_prices.rolling(window=50).mean()
        data[('MA_200', '')] = close_prices.rolling(window=200).mean()
        
        # === MACD ===
        data[('EMA_12', '')] = close_prices.ewm(span=12, adjust=False).mean()
        data[('EMA_26', '')] = close_prices.ewm(span=26, adjust=False).mean()
        data[('MACD', '')] = data[('EMA_12', '')] - data[('EMA_26', '')]
        data[('Signal_Line', '')] = data[('MACD', '')].ewm(span=9, adjust=False).mean()
        data[('MACD_Hist', '')] = data[('MACD', '')] - data[('Signal_Line', '')]
        
        # === RSI ===
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data[('RSI', '')] = 100 - (100 / (1 + rs))
        
        # === 布林带 ===
        data[('BB_Middle', '')] = close_prices.rolling(window=20).mean()
        std = close_prices.rolling(window=20).std()
        data[('BB_Upper', '')] = data[('BB_Middle', '')] + (std * 2)
        data[('BB_Lower', '')] = data[('BB_Middle', '')] - (std * 2)
        data[('BB_Width', '')] = (data[('BB_Upper', '')] - data[('BB_Lower', '')]) / data[('BB_Middle', '')]
        
        # === 随机指标 ===
        low_min = close_prices.rolling(window=14).min()
        high_max = close_prices.rolling(window=14).max()
        data[('Stoch_K', '')] = 100 * (close_prices - low_min) / (high_max - low_min)
        data[('Stoch_D', '')] = data[('Stoch_K', '')].rolling(window=3).mean()
        
        # === ATR (平均真实范围) ===
        if 'High' in data.columns and 'Low' in data.columns:
            high = data['High']
            low = data['Low']
            tr1 = high - low
            tr2 = abs(high - close_prices.shift())
            tr3 = abs(low - close_prices.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            data[('ATR', '')] = tr.rolling(window=14).mean()
        
        # === OBV (能量潮指标) ===
        if 'Volume' in data.columns:
            obv = (close_prices.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0)) * data['Volume']).cumsum()
            data[('OBV', '')] = obv
        
        # === 趋势强度指标 ===
        data[('Trend', '')] = data[('Short_MA', '')] - data[('Long_MA', '')]
        data[('Trend_Strength', '')] = abs(data[('Trend', '')]) / data[('Long_MA', '')] * 100
        data[('Trend_Direction', '')] = np.where(data[('Trend', '')] > 0, 1, -1)
        
        # === 动量指标 ===
        data[('Momentum', '')] = close_prices.diff(periods=10)
        data[('ROC', '')] = close_prices.pct_change(periods=10) * 100
        
        # === 价格偏离度 ===
        data[('Price_Dev_Short', '')] = (close_prices - data[('Short_MA', '')]) / data[('Short_MA', '')] * 100
        data[('Price_Dev_Long', '')] = (close_prices - data[('Long_MA', '')]) / data[('Long_MA', '')] * 100
        
        # === 波动率指标 ===
        data[('Volatility', '')] = close_prices.rolling(window=20).std() / close_prices.rolling(window=20).mean() * 100
        
        # === 信号生成 ===
        # 1. 趋势确认
        trend_confirmed = (data[('MA_50', '')] > data[('MA_200', '')]) & (data[('Short_MA', '')] > data[('Long_MA', '')])
        
        # 2. RSI过滤
        rsi_filter = (data[('RSI', '')] > 30) & (data[('RSI', '')] < 70)
        
        # 3. MACD确认
        macd_signal = data[('MACD_Hist', '')] > 0
        
        # 4. 布林带过滤
        bb_filter = (close_prices > data[('BB_Middle', '')]) & (data[('BB_Width', '')] > 0.1)
        
        # 5. 随机指标过滤
        stoch_filter = (data[('Stoch_K', '')] > data[('Stoch_D', '')]) & (data[('Stoch_K', '')] < 80)
        
        # 6. 波动率过滤
        volatility_filter = data[('Volatility', '')] < data[('Volatility', '')].rolling(window=20).mean()
        
        # 综合信号
        data[('Signal', '')] = np.where(
            trend_confirmed &  # 趋势确认
            rsi_filter &      # RSI过滤
            macd_signal &     # MACD确认
            bb_filter &       # 布林带过滤
            stoch_filter &    # 随机指标过滤
            volatility_filter,# 波动率过滤
            1,               # 买入信号
            np.where(
                (data[('RSI', '')] > 70) |  # RSI超买
                (close_prices < data[('BB_Lower', '')])|  # 突破布林带下轨
                (data[('MACD_Hist', '')] < 0),  # MACD转负
                -1,          # 卖出信号
                0           # 持仓不变
            )
        )
        
        # 在返回数据之前生成交易信号
        signals = generate_trading_signals(data)
        
        # 将信号添加到数据中
        data.loc[data.index[-1], ('Trading_Advice', '')] = signals['summary']
        data.loc[data.index[-1], ('Signal_Strength', '')] = signals['strength']
        data.loc[data.index[-1], ('Signal_Confidence', '')] = signals['confidence']
        data.loc[data.index[-1], ('Trading_Details', '')] = signals['details']
        
        return data
        
    except Exception as e:
        logger.error(f"策略计算出错: {str(e)}")
        logger.debug("错误详情:", exc_info=True)
        return data