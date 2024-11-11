import pandas as pd
import time
from realtime_data import RealTimeData
from strategy import moving_average_strategy
from logger import setup_logger
from config import TICKER, SHORT_WINDOW, LONG_WINDOW, BINANCE_SYMBOL
import yfinance as yf
import threading
import os
import sys
import logging
from datetime import datetime
import locale

# 设置默认编码为UTF-8
if sys.platform.startswith('win'):
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')

def setup_logging():
    """配置日志记录"""
    logger = logging.getLogger('TradingLogger')
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    file_handler = logging.FileHandler('trading_log.txt', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 初始化日志
logger = setup_logging()

def display_data(latest, rt_data):
    """显示最新数据和交易信号"""
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"\n实时市场数据 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 基本价格信息
        print(f"\n价格信息:")
        print("-" * 60)
        print(f"当前价格:     {latest[('Close', TICKER)]:.5f}")
        print(f"短期MA({SHORT_WINDOW}):   {latest[('Short_MA', '')]:.5f}")
        print(f"长期MA({LONG_WINDOW}):  {latest[('Long_MA', '')]:.5f}")
        
        # MACD指标
        print(f"\nMACD指标:")
        print("-" * 60)
        print(f"MACD:         {latest[('MACD', '')]:.5f}")
        print(f"信号线:       {latest[('Signal_Line', '')]:.5f}")
        print(f"MACD柱状:     {latest[('MACD_Hist', '')]:.5f}")
        
        # RSI指标
        print(f"\nRSI指标:")
        print("-" * 60)
        print(f"RSI(14):      {latest[('RSI', '')]:.2f}")
        rsi_signal = "超卖" if latest[('RSI', '')] < 30 else "超买" if latest[('RSI', '')] > 70 else "中性"
        print(f"RSI信号:      {rsi_signal}")
        
        # 布林带
        print(f"\n布林带:")
        print("-" * 60)
        print(f"上轨:         {latest[('BB_Upper', '')]:.5f}")
        print(f"中轨:         {latest[('BB_Middle', '')]:.5f}")
        print(f"下轨:         {latest[('BB_Lower', '')]:.5f}")
        
        # 趋势分析
        print(f"\n趋势分析:")
        print("-" * 60)
        trend = "上升" if latest[('Trend', '')] > 0 else "下降"
        trend_strength = latest[('Trend_Strength', '')]
        print(f"当前趋势:     {trend}")
        print(f"趋势强度:     {trend_strength:.2f}%")
        print(f"动量:         {latest[('Momentum', '')]:.5f}")
        
        # 价格偏离度
        print(f"\n价格偏离度:")
        print("-" * 60)
        print(f"距短期MA:     {latest[('Price_Dev_Short', '')]:.2f}%")
        print(f"距长期MA:     {latest[('Price_Dev_Long', '')]:.2f}%")
        
        # 交易信号
        print(f"\n交易信号:")
        print("-" * 60)
        signal = latest[('Signal', '')]
        signal_text = "买入" if signal == 1 else "卖出" if signal == -1 else "持有"
        print(f"主要信号:     {signal_text}")
        
        # 综合建议
        print(f"\n综合分析:")
        print("-" * 60)
        
        # 基于多个指标的综合分析
        bullish_signals = 0
        bearish_signals = 0
        
        # MACD信号
        if latest[('MACD_Hist', '')] > 0:
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        # RSI信号
        if latest[('RSI', '')] < 30:
            bullish_signals += 1
        elif latest[('RSI', '')] > 70:
            bearish_signals += 1
            
        # 布林带信号
        price = latest[('Close', TICKER)]
        if price < latest[('BB_Lower', '')]:
            bullish_signals += 1
        elif price > latest[('BB_Upper', '')]:
            bearish_signals += 1
            
        # 趋势信号
        if latest[('Trend', '')] > 0:
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        # 输出综合建议
        total_signals = bullish_signals + bearish_signals
        bull_strength = (bullish_signals / total_signals) * 100 if total_signals > 0 else 0
        
        print(f"看涨信号:     {bullish_signals}")
        print(f"看跌信号:     {bearish_signals}")
        print(f"多头强度:     {bull_strength:.1f}%")
        
        if bull_strength > 60:
            print("建议:         可以考虑买入")
        elif bull_strength < 40:
            print("建议:         可以考虑卖出")
        else:
            print("建议:         建议观望")
            
        # 风险提示
        if abs(latest[('Price_Dev_Short', '')]) > 5:
            print("\n风险提示:     价格偏离均线过大，注意风险")
        if latest[('RSI', '')] > 75 or latest[('RSI', '')] < 25:
            print("风险提示:     RSI处于极值区域，注意反转风险")
        
        print("=" * 60)
        sys.stdout.flush()  # 确保输出被立即显示
    except Exception as e:
        logger.error(f"显示数据时出错: {str(e)}")

def main():
    try:
        # 初始化数据
        data = yf.download(TICKER, start='2024-01-01')
        if data.empty:
            logger.error(f"无法获取 {TICKER} 的历史数据")
            return
            
        data = data[['Close']]
        data.columns = pd.MultiIndex.from_tuples([('Close', TICKER)])
        
        # 应用策略
        data_with_signals = moving_average_strategy(data, SHORT_WINDOW, LONG_WINDOW)
        
        # 初始化实时数据流
        rt_data = RealTimeData(TICKER)
        
        # 在新线程中启动WebSocket
        ws_thread = threading.Thread(target=rt_data.start_stream)
        ws_thread.daemon = True
        ws_thread.start()
        
        logger.info(f"Starting real-time data stream for {TICKER}")
        
        last_price = None
        while True:
            if rt_data.price and rt_data.price != last_price:
                current_price = rt_data.price
                last_price = current_price
                
                try:
                    # 创建新的数据行
                    new_row = pd.DataFrame({
                        ('Close', TICKER): [current_price]
                    }, index=[pd.Timestamp.now()])
                    
                    # 更新数据
                    data_with_signals = pd.concat([data_with_signals, new_row])
                    data_with_signals = moving_average_strategy(
                        data_with_signals.tail(1000),
                        SHORT_WINDOW, 
                        LONG_WINDOW
                    )
                    
                    # 显示数据
                    display_data(data_with_signals.iloc[-1], rt_data)
                    
                except Exception as e:
                    logger.error(f"处理数据时出错: {str(e)}")
                    
            time.sleep(0.1)  # 减少CPU使用
            
    except KeyboardInterrupt:
        logger.info("User interrupted the stream. Closing.")
        rt_data.stop_stream()
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        rt_data.stop_stream()

if __name__ == "__main__":
    main()