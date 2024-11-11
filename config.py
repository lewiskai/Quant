# config.py

# 交易对信息
TICKER = 'DOGE-USD'  # Yahoo Finance 格式
BINANCE_SYMBOL = 'dogeusdt'  # Binance 格式

# 数据时间范围
START_DATE = '2020-01-01'
END_DATE = '2024-11-11'

# 策略参数
SHORT_WINDOW = 20  # 短期均线窗口
LONG_WINDOW = 50  # 长期均线窗口

# 日志配置
LOG_FILE = 'trading_log.txt'  # 日志文件路径
LOG_LEVEL = 'DEBUG'  # 临时改为 DEBUG 以获取更多信息

# 交易参数
TRADE_AMOUNT = 100  # 每次交易的USDT金额
STOP_LOSS_PERCENT = 2.0  # 止损百分比
TAKE_PROFIT_PERCENT = 4.0  # 止盈百分比
MAX_POSITIONS = 3  # 最大持仓数量

# WebSocket配置
WEBSOCKET_TIMEOUT = 30  # WebSocket超时时间（秒）
WEBSOCKET_RETRY = 3    # 重试次数
WEBSOCKET_RECONNECT = True
WEBSOCKET_PING_INTERVAL = 30
WEBSOCKET_PING_TIMEOUT = 10

# 添加新的配置项
TRADE_CONFIG = {
    'max_daily_trades': 10,      # 每日最大交易次数
    'min_profit_target': 1.5,    # 最小获利目标(%)
    'max_spread': 0.1,           # 最大允许价差(%)
    'trading_hours': {           # 交易时间段
        'start': '00:00',
        'end': '23:59'
    }
}

# 风险控制参数
RISK_CONFIG = {
    'max_daily_loss': -5.0,      # 每日最大亏损限制(%)
    'position_sizing': 0.2,      # 单个仓位最大资金比例
    'max_drawdown': 20,          # 最大回撤限制(%)
    'min_volume': 100            # 最小交易量
}