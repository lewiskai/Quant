# data_loader.py

import yfinance as yf
import pandas as pd

def load_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取指定交易对的历史数据。

    参数:
    - ticker: str, 如 "DOGE-USD"
    - start_date: str, 数据开始日期，格式 "YYYY-MM-DD"
    - end_date: str, 数据结束日期，格式 "YYYY-MM-DD"

    返回:
    - pd.DataFrame, 包含历史收盘价的 DataFrame
    """
    try:
        # 从 Yahoo Finance 下载数据
        data = yf.download(ticker, start=start_date, end=end_date)
        
        # 检查数据是否成功下载
        if data.empty:
            print(f"没有找到 {ticker} 的数据.")
            return None
        
        # 保留收盘价列，并重命名为 'Close'
        data = data[['Close']]
        data.dropna(inplace=True)  # 移除缺失值
        print(f"成功加载 {ticker} 的数据，包含 {len(data)} 条记录.")
        
        return data

    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None