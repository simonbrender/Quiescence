"""
Test Portfolios Endpoint - Validate it works correctly
"""
import requests
import json

def test_portfolios_endpoint():
    """Test the /portfolios endpoint"""
    
    print("\n" + "="*80)
    print("VALIDATING PORTFOLIOS ENDPOINT")
    print("="*80 + "\n")
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check backend is running
    print("[1/4] Checking backend server...")
    try:
        stats_response = requests.get(f"{base_url}/stats", timeout=5)
        if stats_response.status_code == 200:
            print("   [OK] Backend server is running")
        else:
            print(f"   [FAIL] Backend returned status {stats_response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   [FAIL] Backend server is NOT running")
        print("   -> Start it with: python backend/main.py")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 2: Get all portfolios
    print("\n[2/4] Testing GET /portfolios...")
    try:
        response = requests.get(f"{base_url}/portfolios", timeout=10)
        if response.status_code == 200:
            portfolios = response.json()
            print(f"   [OK] Success: Found {len(portfolios)} portfolios")
            
            if len(portfolios) > 0:
                print(f"\n   Sample portfolios:")
                for i, p in enumerate(portfolios[:5], 1):
                    print(f"     {i}. {p.get('firm_name', 'Unknown')} ({p.get('type', 'Unknown')})")
                if len(portfolios) > 5:
                    print(f"     ... and {len(portfolios) - 5} more")
            else:
                print("   [WARN] No portfolios found in database")
        else:
            print(f"   [FAIL] Failed: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 3: Test filtered portfolios
    print("\n[3/4] Testing GET /portfolios with filters...")
    try:
        # Test stage filter
        response = requests.get(f"{base_url}/portfolios?stage=Seed", timeout=10)
        if response.status_code == 200:
            filtered = response.json()
            print(f"   [OK] Stage filter (Seed): {len(filtered)} portfolios")
        
        # Test type filter
        response = requests.get(f"{base_url}/portfolios?vc_type=VC", timeout=10)
        if response.status_code == 200:
            filtered = response.json()
            print(f"   [OK] Type filter (VC): {len(filtered)} portfolios")
    except Exception as e:
        print(f"   [FAIL] Filter test error: {e}")
    
    # Test 4: Check required fields
    print("\n[4/4] Validating portfolio structure...")
    try:
        response = requests.get(f"{base_url}/portfolios", timeout=10)
        portfolios = response.json()
        
        if len(portfolios) > 0:
            sample = portfolios[0]
            required_fields = ['firm_name', 'type', 'stage']
            missing_fields = [f for f in required_fields if f not in sample]
            
            if missing_fields:
                print(f"   [FAIL] Missing fields: {missing_fields}")
                return False
            else:
                print(f"   [OK] All required fields present")
                print(f"   Fields: {list(sample.keys())}")
        else:
            print("   [WARN] No portfolios to validate structure")
    except Exception as e:
        print(f"   [FAIL] Validation error: {e}")
        return False
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_portfolios_endpoint()
    exit(0 if success else 1)

