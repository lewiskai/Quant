# strategy.py

import pandas as pd
import logging
import numpy as np
from datetime import datetime

# 配置日志记录器
logger = logging.getLogger(__name__)

def generate_trading_signals(data: pd.DataFrame) -> dict:
    """
    Generate trading signals and recommendations with improved strategy
    """
    try:
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else None
        
        close_price = float(latest['close'])
        
        signals = {
            'price': close_price,
            'signal': 0,
            'strength': 0,
            'confidence': 0,
            'reasons': [],
            'risks': []
        }

        # Trend Analysis
        short_ma = float(latest['SMA_short'])
        long_ma = float(latest['SMA_long'])
        ma_50 = float(latest['MA_50'])
        ma_200 = float(latest['MA_200'])
        
        # MACD Analysis
        macd = float(latest['MACD'])
        macd_signal = float(latest['Signal_Line'])
        macd_hist = float(latest['MACD_Hist'])
        
        # RSI Analysis
        rsi = float(latest['RSI'])
        
        # Bollinger Bands
        bb_upper = float(latest['BB_Upper'])
        bb_lower = float(latest['BB_Lower'])
        
        # Volume Analysis
        volume = float(latest['volume'])
        avg_volume = float(latest['Volume_MA'])

        # Trend Confirmation (更严格的条件)
        if short_ma > long_ma and ma_50 > ma_200 and close_price > ma_50:
            signals['reasons'].append("Strong uptrend confirmed")
            signals['strength'] += 20
            signals['signal'] = 1
        elif short_ma < long_ma and ma_50 < ma_200 and close_price < ma_50:
            signals['reasons'].append("Strong downtrend confirmed")
            signals['strength'] -= 20
            signals['signal'] = -1

        # MACD Signal (增加确认条件)
        if macd > macd_signal and macd_hist > 0 and macd_hist > prev['MACD_Hist']:
            signals['reasons'].append("MACD indicates increasing bullish momentum")
            signals['strength'] += 15
            signals['signal'] = max(signals['signal'], 0) + 1
        elif macd < macd_signal and macd_hist < 0 and macd_hist < prev['MACD_Hist']:
            signals['reasons'].append("MACD indicates increasing bearish momentum")
            signals['strength'] -= 15
            signals['signal'] = min(signals['signal'], 0) - 1

        # RSI Overbought/Oversold (调整阈值)
        if rsi > 75:
            signals['risks'].append("RSI indicates strong overbought conditions")
            signals['strength'] -= 15
        elif rsi < 25:
            signals['reasons'].append("RSI indicates strong oversold conditions")
            signals['strength'] += 15

        # Bollinger Bands Breakout (增加确认条件)
        if close_price > bb_upper and volume > avg_volume * 1.2:
            signals['risks'].append("Price above upper Bollinger Band with high volume, potential reversal")
            signals['strength'] -= 10
        elif close_price < bb_lower and volume > avg_volume * 1.2:
            signals['reasons'].append("Price below lower Bollinger Band with high volume, potential buying opportunity")
            signals['strength'] += 10

        # Volume Confirmation (增加条件)
        if volume > avg_volume * 2:
            signals['reasons'].append("Extremely high volume confirms the move")
            signals['strength'] = signals['strength'] * 1.3 if signals['strength'] > 0 else signals['strength'] * 0.7

        # Determine final signal (调整阈值)
        if signals['strength'] > 40:
            signals['signal'] = 1  # Strong Buy
        elif signals['strength'] > 20:
            signals['signal'] = 0.5  # Buy
        elif signals['strength'] < -40:
            signals['signal'] = -1  # Strong Sell
        elif signals['strength'] < -20:
            signals['signal'] = -0.5  # Sell
        else:
            signals['signal'] = 0  # Hold

        # Calculate final confidence
        signals['confidence'] = min(100, max(0, abs(signals['strength'])))
        
        return signals
        
    except Exception as e:
        logger.error(f"Error in signal generation: {str(e)}")
        return {
            'price': 0,
            'signal': 0,
            'strength': 0,
            'confidence': 0,
            'reasons': [],
            'risks': []
        }

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