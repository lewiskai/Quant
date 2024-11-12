# Crypto Trading Bot

A Python-based cryptocurrency trading bot that supports real-time market data streaming, automated trading strategies, backtesting, and paper trading capabilities.

## Features

- Real-time market data streaming from crypto exchanges
- Multiple trading strategies implementation
- Risk management system
- Paper trading simulation
- Backtesting framework
- Performance tracking and analysis
- Interactive data visualization
- Comprehensive logging system

## Prerequisites

- Python 3.8+
- Valid API keys from supported cryptocurrency exchanges

## Installation

1. Clone the repository:

bash
git clone https://github.com/lewiskai/Quant.git
cd crypto-trading-bot

2. Install required packages:

bash
pip install -r requirements.txt

3. Create a `.env` file in the root directory with your API credentials:

bash
API_KEY=your_api_key
API_SECRET=your_api_secret
TICKER=DOGE-USD

## Project Structure

- `main.py`: Main entry point for the trading bot
- `realtime_data.py`: Handles real-time market data streaming
- `strategy.py`: Implements trading strategies
- `risk_manager.py`: Manages trading risks and position sizing
- `backtest.py`: Backtesting framework
- `performance_tracker.py`: Tracks and analyzes trading performance
- `plot.py`: Visualization utilities
- `trading.py`: Order execution and management

## Features in Detail

### Real-time Data
- WebSocket connection for live market data
- Real-time price updates and indicator calculations

### Trading Strategies
- Moving Average Crossover
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)

### Risk Management
- Position sizing
- Stop-loss and take-profit orders
- Maximum drawdown protection
- Daily loss limits

### Paper Trading
- Simulated trading with virtual balance
- Performance tracking
- Trade history logging

### Backtesting
- Historical data analysis
- Strategy performance evaluation
- Risk metrics calculation
- Visual performance reports

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.
