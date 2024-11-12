# logger.py

import logging
import sys

def setup_logger():
    """Setup and configure logger with proper encoding"""
    logger = logging.getLogger('TradingLogger')
    logger.setLevel(logging.DEBUG)
    
    # File handler with UTF-8 encoding
    fh = logging.FileHandler('trading_log.txt', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger