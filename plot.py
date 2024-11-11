import matplotlib.pyplot as plt
import pandas as pd

def plot_results(data: pd.DataFrame):
    """绘制交易结果图表
    
    Args:
        data (DataFrame): 包含价格、移动平均线和信号的数据
    """
    plt.figure(figsize=(12, 6))
    plt.plot(data[('Close', data.columns.get_level_values(1)[0])], label='价格')
    plt.plot(data[('Short_MA', '')], label='短期MA')
    plt.plot(data[('Long_MA', '')], label='长期MA')
    plt.title('交易策略回测结果')
    plt.legend()
    plt.show() 