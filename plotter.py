# plotter.py

import matplotlib.pyplot as plt
import pandas as pd

def plot_results(data: pd.DataFrame):
    """
    绘制策略的累计收益曲线，与市场的累计收益进行比较。

    参数:
    - data: pd.DataFrame, 包含市场和策略累计收益的 DataFrame
    """
    plt.figure(figsize=(12, 6))

    # 绘制市场累计收益曲线
    plt.plot(data['Market_Cumulative'], label='Market Cumulative Return', linestyle='-', linewidth=1.5)

    # 绘制策略累计收益曲线
    plt.plot(data['Strategy_Cumulative'], label='Strategy Cumulative Return', linestyle='--', linewidth=1.5)

    # 添加标题和标签
    plt.title('Cumulative Returns Comparison')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.grid(True)

    # 显示图表
    plt.show()