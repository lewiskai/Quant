# strategy.py

import pandas as pd
import logging
import numpy as np

# 配置日志记录器
logger = logging.getLogger(__name__)

def generate_trading_signals(data: pd.DataFrame) -> dict:
    """
    生成交易信号和建议
    
    返回:
    - dict: 包含交易信号和详细分析的字典
    """
    latest = data.iloc[-1]
    prev = data.iloc[-2] if len(data) > 1 else None
    
    # 获取基础数据
    close_price = latest[('Close', data.columns.get_level_values(1)[0])]
    
    signals = {
        'price': close_price,
        'signal': latest[('Signal', '')],
        'strength': 0,  # 信号强度 (0-100)
        'confidence': 0,  # 置信度 (0-100)
        'reasons': [],  # 建议原因
        'risks': [],    # 风险提示
        'supports': [], # 支撑位
        'resistances': [], # 阻力位
        'stop_loss': None, # 建议止损
        'take_profit': None # 建议止盈
    }
    
    # === 趋势分析 ===
    if latest[('Short_MA', '')] > latest[('Long_MA', '')]:
        signals['reasons'].append("短期均线位于长期均线上方，趋势向上")
        signals['strength'] += 20
    else:
        signals['reasons'].append("短期均线位于长期均线下方，趋势向下")
        signals['strength'] -= 20
        
    # === MACD分析 ===
    if latest[('MACD_Hist', '')] > 0:
        if prev and latest[('MACD_Hist', '')] > prev[('MACD_Hist', '')]:
            signals['reasons'].append("MACD柱状图增长，买入动能增强")
            signals['strength'] += 15
    else:
        signals['reasons'].append("MACD柱状图为负，可能存在下跌风险")
        signals['risks'].append("MACD显示下跌趋势")
        
    # === RSI分析 ===
    rsi = latest[('RSI', '')]
    if rsi > 70:
        signals['risks'].append(f"RSI超买（{rsi:.1f}），注意回调风险")
        signals['strength'] -= 10
    elif rsi < 30:
        signals['reasons'].append(f"RSI超卖（{rsi:.1f}），可能存在反弹机会")
        signals['strength'] += 10
        
    # === 布林带分析 ===
    bb_width = latest[('BB_Width', '')]
    if close_price > latest[('BB_Upper', '')]:
        signals['risks'].append("价格突破布林带上轨，注意回调")
        signals['strength'] -= 15
    elif close_price < latest[('BB_Lower', '')]:
        signals['reasons'].append("价格突破布林带下轨，可能存在反弹")
        signals['strength'] += 15
        
    if bb_width > 0.1:
        signals['reasons'].append("布林带扩张，趋势走强")
    else:
        signals['risks'].append("布林带收窄，可能即将突破")
        
    # === 支撑阻力位计算 ===
    signals['supports'] = [
        latest[('BB_Lower', '')],
        latest[('Long_MA', '')],
        latest[('Short_MA', '')]
    ]
    signals['resistances'] = [
        latest[('BB_Upper', '')],
        latest[('Long_MA', '')],
        latest[('Short_MA', '')]
    ]
    
    # === 止损止盈建议 ===
    atr = latest[('ATR', '')] if ('ATR', '') in latest else (latest[('BB_Upper', '')] - latest[('BB_Lower', '')]) / 2
    signals['stop_loss'] = close_price - (atr * 2)
    signals['take_profit'] = close_price + (atr * 3)
    
    # === 计算置信度 ===
    signals['confidence'] = min(100, max(0, signals['strength']))
    
    # === 生成建议摘要 ===
    if signals['signal'] == 1:
        reasons_text = '\n'.join(['• ' + r for r in signals['reasons']])
        risks_text = '\n'.join(['• ' + r for r in signals['risks']])
        supports_text = '\n'.join([f'• {s:.5f}' for s in signals['supports']])
        resistances_text = '\n'.join([f'• {r:.5f}' for r in signals['resistances']])
        
        signals['summary'] = "建议买入"
        signals['details'] = (
            f"交易建议：买入\n"
            f"价格：{close_price:.5f}\n"
            f"建议止损：{signals['stop_loss']:.5f}\n"
            f"建议止盈：{signals['take_profit']:.5f}\n"
            f"信号强度：{signals['strength']}%\n"
            f"置信度：{signals['confidence']}%\n\n"
            f"做多理由：\n{reasons_text}\n\n"
            f"风险提示：\n{risks_text}\n\n"
            f"支撑位：\n{supports_text}\n\n"
            f"阻力位：\n{resistances_text}"
        )
    elif signals['signal'] == -1:
        reasons_text = '\n'.join(['• ' + r for r in signals['reasons']])
        risks_text = '\n'.join(['• ' + r for r in signals['risks']])
        
        signals['summary'] = "建议卖出"
        signals['details'] = (
            f"交易建议：卖出\n"
            f"价格：{close_price:.5f}\n"
            f"信号强度：{signals['strength']}%\n"
            f"置信度：{signals['confidence']}%\n\n"
            f"卖出理由：\n{reasons_text}\n\n"
            f"风险提示：\n{risks_text}"
        )
    else:
        reasons_text = '\n'.join(['• ' + r for r in signals['reasons']])
        risks_text = '\n'.join(['• ' + r for r in signals['risks']])
        
        signals['summary'] = "建议观望"
        signals['details'] = (
            f"交易建议：观望\n"
            f"当前价格：{close_price:.5f}\n"
            f"信号强度：{signals['strength']}%\n"
            f"置信度：{signals['confidence']}%\n\n"
            f"市场分析：\n{reasons_text}\n\n"
            f"需注意：\n{risks_text}"
        )
    
    return signals

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