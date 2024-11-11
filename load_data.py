import yfinance as yf
import pandas as pd

def load_data(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        data = data[['Close']]
        data.columns = pd.MultiIndex.from_tuples([('Close', ticker)])
        return data
    except Exception as e:
        print(f"加载数据时出错: {str(e)}")
        return None 