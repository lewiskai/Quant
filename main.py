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
        
        # 显示交易建议
        if ('Trading_Advice', '') in latest:
            print(f"\n交易建议:")
            print("-" * 60)
            print(latest[('Trading_Details', '')])
            
        # 基本价格信息
        print(f"\n价格信息:")
        print("-" * 60)
        print(f"当前价格:     {latest[('Close', TICKER)]:.5f}")
        
        # 检查并显示移动平均线
        if ('Short_MA', '') in latest:
            print(f"短期MA({SHORT_WINDOW}):   {latest[('Short_MA', '')]:.5f}")
        if ('Long_MA', '') in latest:
            print(f"长期MA({LONG_WINDOW}):  {latest[('Long_MA', '')]:.5f}")
        
        # MACD指标
        if all(x in latest for x in [('MACD', ''), ('Signal_Line', ''), ('MACD_Hist', '')]):
            print(f"\nMACD指标:")
            print("-" * 60)
            print(f"MACD:         {latest[('MACD', '')]:.5f}")
            print(f"信号线:       {latest[('Signal_Line', '')]:.5f}")
            print(f"MACD柱状:     {latest[('MACD_Hist', '')]:.5f}")
        
        # RSI指标
        if ('RSI', '') in latest:
            print(f"\nRSI指标:")
            print("-" * 60)
            print(f"RSI(14):      {latest[('RSI', '')]:.2f}")
            rsi_signal = "超卖" if latest[('RSI', '')] < 30 else "超买" if latest[('RSI', '')] > 70 else "中性"
            print(f"RSI信号:      {rsi_signal}")
        
        # 布林带
        if all(x in latest for x in [('BB_Upper', ''), ('BB_Middle', ''), ('BB_Lower', '')]):
            print(f"\n布林带:")
            print("-" * 60)
            print(f"上轨:         {latest[('BB_Upper', '')]:.5f}")
            print(f"中轨:         {latest[('BB_Middle', '')]:.5f}")
            print(f"下轨:         {latest[('BB_Lower', '')]:.5f}")
        
        # 趋势分析
        if ('Trend', '') in latest:
            print(f"\n趋势分析:")
            print("-" * 60)
            trend = "上升" if latest[('Trend', '')] > 0 else "下降"
            print(f"当前趋势:     {trend}")
            
            if ('Trend_Strength', '') in latest:
                print(f"趋势强度:     {latest[('Trend_Strength', '')]:.2f}%")
            if ('Momentum', '') in latest:
                print(f"动量:         {latest[('Momentum', '')]:.5f}")
        
        # 价格偏离度
        print(f"\n价格偏离度:")
        print("-" * 60)
        
        # 计算价格偏离度
        if ('Short_MA', '') in latest:
            short_dev = (latest[('Close', TICKER)] - latest[('Short_MA', '')]) / latest[('Short_MA', '')] * 100
            print(f"距短期MA:     {short_dev:.2f}%")
        
        if ('Long_MA', '') in latest:
            long_dev = (latest[('Close', TICKER)] - latest[('Long_MA', '')]) / latest[('Long_MA', '')] * 100
            print(f"距长期MA:     {long_dev:.2f}%")
        
        print("=" * 60)
        sys.stdout.flush()
        
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