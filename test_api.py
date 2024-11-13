import requests
import time
import hmac
import hashlib
import json

API_KEY = "QjD5qQnq7dCvt1gmxTPr83"
API_SECRET = "cxakp_ETe5i18KdeKD73NRXXDGeh"

def test_api_access():
    base_url = "https://api.crypto.com/v2"
    
    # Test public endpoint first
    request_id = str(int(time.time() * 1000))
    
    # 1. Test public instruments endpoint
    public_params = {
        "id": request_id,
        "method": "public/get-instruments",
        "nonce": int(time.time() * 1000)
    }
    
    print("Testing public endpoint...")
    response = requests.post(
        f"{base_url}/public/get-instruments",
        json=public_params,
        headers={"Content-Type": "application/json"}
    )
    print(f"Public Response: {response.status_code}")
    print(response.json())
    
    # 2. Test private endpoint
    private_params = {
        "id": request_id,
        "method": "private/get-account-summary",
        "api_key": API_KEY,
        "params": {},
        "nonce": int(time.time() * 1000)
    }
    
    # Generate signature
    sig_str = f"{private_params['method']}{private_params['id']}{private_params['api_key']}{private_params['nonce']}"
    private_params["sig"] = hmac.new(
        bytes(API_SECRET, 'utf-8'),
        sig_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print("\nTesting private endpoint...")
    response = requests.post(
        f"{base_url}/private/get-account-summary",
        json=private_params,
        headers={"Content-Type": "application/json"}
    )
    print(f"Private Response: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    test_api_access() 