import socket
import requests

def test_connection():
    try:
        # Test DNS resolution
        ip = socket.gethostbyname('api.crypto.com')
        print(f"DNS Resolution successful. IP: {ip}")
        
        # Test API connection
        response = requests.get('https://api.crypto.com/v2/public/get-instruments')
        print(f"API Connection successful. Status code: {response.status_code}")
        
    except socket.gaierror as e:
        print(f"DNS resolution failed: {e}")
    except requests.exceptions.RequestException as e:
        print(f"API connection failed: {e}")

if __name__ == "__main__":
    test_connection() 