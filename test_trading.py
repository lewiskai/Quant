from dotenv import load_dotenv
import os
from crypto_api import CryptoComAPI

def test_trading_functions():
    load_dotenv()
    api = CryptoComAPI(os.getenv('API_KEY'), os.getenv('API_SECRET'))
    
    try:
        # 测试获取市场价格
        print("Getting market price...")
        price = api.get_market_price()
        print(f"Current DOGE price: {price}")
        
        # 测试下单功能
        print("\nTesting order creation...")
        test_order = api.create_order(
            side="BUY",
            price="0.399200",
            quantity="100"  # 测试性下100个DOGE的单
        )
        print(f"Test order result: {test_order}")
        
        if test_order.get('code') == 0:
            print("Order creation successful!")
            # 立即取消测试订单
            cancel_result = api.cancel_order(test_order['result']['order_id'])
            print(f"Test order cancelled: {cancel_result}")
            
    except Exception as e:
        print(f"Error in testing: {str(e)}")

if __name__ == "__main__":
    test_trading_functions()
