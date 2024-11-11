# logger.py

import logging
import config

def setup_logger():
    """
    设置日志记录器。
    返回: logger 对象
    """
    # 创建logger
    logger = logging.getLogger('TradingLogger')
    logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # 创建文件处理器并设置日志格式
    file_handler = logging.FileHandler(config.LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # 将处理器添加到logger
    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger