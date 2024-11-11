# realtime_data.py

import json
import websocket
import threading
import time
import logging
import ssl
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RealTimeData")

class RealTimeData:
    def __init__(self, symbol="DOGE-USD", max_reconnects=5):
        """
        初始化实时数据流
        Args:
            symbol: 交易对符号，例如 "DOGE-USD"
            max_reconnects: 最大重连次数
        """
        self.symbol = symbol
        self.binance_symbol = "dogeusdt"  # 使用小写
        self.price = None
        self.ws = None
        self.reconnect_attempts = 0
        self.max_reconnects = max_reconnects
        self.price_history = []
        self.max_history_size = 200
        self.logger = logging.getLogger('RealTimeData')
        self.last_update_time = None
        self.running = True
        self.last_ping_time = time.time()
        self.ping_interval = 20
        self.connection_timeout = 30

    def on_message(self, ws, message):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            
            # 更新最后ping时间
            self.last_ping_time = time.time()
            
            if 'result' in data and data['result'] is None:
                self.logger.info("订阅确认成功")
                return
                
            if 'e' in data:
                if data['e'] == 'kline':
                    kline = data['k']
                    current_price = float(kline['c'])
                    current_time = pd.Timestamp.fromtimestamp(data['E'] / 1000)
                    
                    if self.price != current_price:
                        self.price = current_price
                        self.last_update_time = current_time
                        self.logger.info(f"价格更新: {current_price} @ {current_time}")
                        self.process_price_update(current_price)
                else:
                    self.logger.debug(f"收到其他事件: {data['e']}")
                    
        except json.JSONDecodeError:
            self.logger.error(f"JSON解析错误: {message}")
        except Exception as e:
            self.logger.error(f"处理消息时出错: {str(e)}")

    def on_error(self, ws, error):
        logger.error(f"WebSocket错误: {error}")
        if isinstance(error, websocket.WebSocketConnectionClosedException):
            if self.running:
                self._reconnect()

    def on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket连接关闭")
        if self.running:
            self._reconnect()

    def on_open(self, ws):
        """WebSocket连接建立时的回调"""
        self.logger.info("WebSocket连接已建立")
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params": [
                f"{self.binance_symbol}@kline_1m"
            ],
            "id": int(time.time())  # 使用时间戳作为唯一ID
        }
        self.logger.info(f"发送订阅请求: {subscribe_message}")
        ws.send(json.dumps(subscribe_message))
        self.last_ping_time = time.time()

    def start_stream(self):
        """启动WebSocket流"""
        self.running = True
        while self.running:
            try:
                # websocket.enableTrace(True)  # 注释掉过多的调试信息
                self.ws = websocket.WebSocketApp(
                    "wss://stream.binance.com:9443/ws",
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                    on_open=self.on_open,
                    on_ping=self.on_ping,
                    on_pong=self.on_pong
                )
                
                self.logger.info("正在连接到 Binance WebSocket...")
                
                # 启动心跳检查线程
                self._start_heartbeat()
                
                self.ws.run_forever(
                    ping_interval=self.ping_interval,
                    ping_timeout=10,
                    sslopt={"cert_reqs": ssl.CERT_NONE}
                )
                
                if not self.running:
                    break
                
            except Exception as e:
                self.logger.error(f"WebSocket连接出错: {str(e)}")
                if self.running:
                    self._reconnect()
                else:
                    break

    def _start_heartbeat(self):
        """启动心跳检查"""
        def heartbeat():
            while self.running:
                if time.time() - self.last_ping_time > self.connection_timeout:
                    self.logger.warning("心跳超时，重新连接...")
                    self.ws.close()
                    break
                time.sleep(1)
        
        heartbeat_thread = threading.Thread(target=heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()

    def _reconnect(self):
        """重新连接逻辑"""
        if self.reconnect_attempts < self.max_reconnects:
            wait_time = min(5 * (2 ** self.reconnect_attempts), 30)
            self.logger.info(f"等待 {wait_time} 秒后重新连接...")
            time.sleep(wait_time)
            self.reconnect_attempts += 1
            self.start_stream()
        else:
            self.logger.error("达到最大重连次数，停止重连")
            self.running = False

    def on_ping(self, ws, message):
        """处理ping消息"""
        self.last_ping_time = time.time()
        self.logger.debug("收到ping")

    def on_pong(self, ws, message):
        """处理pong消息"""
        self.last_ping_time = time.time()
        self.logger.debug("收到pong")

    def process_price_update(self, price):
        """处理价格更新"""
        self.price = price
        self.price_history.append(price)
        
        # 保持历史数据在限定范围内
        if len(self.price_history) > self.max_history_size:
            self.price_history.pop(0)