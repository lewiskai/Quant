import matplotlib.pyplot as plt
import pandas as pd

def plot_results(data: pd.DataFrame):
    """Plot trading results
    
    Args:
        data (DataFrame): DataFrame containing prices, moving averages and signals
    """
    plt.figure(figsize=(12, 6))
    plt.plot(data[('Close', data.columns.get_level_values(1)[0])], label='Price')
    plt.plot(data[('Short_MA', '')], label='Short MA')
    plt.plot(data[('Long_MA', '')], label='Long MA')
    plt.title('Trading Strategy Backtest Results')
    plt.legend()
    plt.show() 