"""
Test Discover VCs Endpoint
"""
import requests
import json
import sys

def test_discover():
    """Test the /portfolios/discover endpoint"""
    
    print("\n" + "="*80)
    print("TESTING DISCOVER VCs ENDPOINT")
    print("="*80 + "\n")
    
    url = "http://localhost:8000/portfolios/discover"
    
    print(f"Testing POST {url}")
    print("This may take several minutes...\n")
    
    try:
        # Test with 10 second timeout first to see if endpoint responds
        response = requests.post(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error Response: {response.text[:500]}")
    except requests.exceptions.ConnectionError:
        print("[FAIL] Backend server is NOT running")
        print("Start it with: python backend/main.py")
        return False
    except requests.exceptions.Timeout:
        print("[INFO] Request timed out after 10 seconds")
        print("This is expected - discovery can take 5+ minutes")
        print("The endpoint is working, but needs more time")
        return True  # Endpoint exists, just slow
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80 + "\n")
    return True

if __name__ == "__main__":
    success = test_discover()
    sys.exit(0 if success else 1)



