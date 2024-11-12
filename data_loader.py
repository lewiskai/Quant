# data_loader.py

import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def load_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Load historical data for specified trading pair.

    Args:
    - ticker: str, e.g., "DOGE-USD"
    - start_date: str, start date in "YYYY-MM-DD" format
    - end_date: str, end date in "YYYY-MM-DD" format

    Returns:
    - pd.DataFrame with historical closing prices
    """
    try:
        # Download data from Yahoo Finance
        data = yf.download(ticker, start=start_date, end=end_date)
        
        if data.empty:
            logger.error(f"No data found for {ticker}")
            return None
        
        # Create multi-level column index
        data = data[['Close']]
        data.columns = pd.MultiIndex.from_product([['Close'], [ticker]])
        data.dropna(inplace=True)
        
        logger.info(f"Successfully loaded {len(data)} records for {ticker}")
        return data

    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return None