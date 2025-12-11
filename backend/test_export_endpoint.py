"""Test the export endpoint to ensure it returns all companies"""
import requests
import json
import time

def test_export_endpoint(max_retries=10, retry_delay=2):
    """Test the export endpoint with retries"""
    base_url = "http://localhost:8000"
    
    print("="*60)
    print("TESTING EXPORT ENDPOINT")
    print("="*60)
    
    # Wait for backend to be ready
    for attempt in range(max_retries):
        try:
            # Test if backend is up
            response = requests.get(f"{base_url}/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                print(f"[OK] Backend is running")
                print(f"     Total companies in DB: {stats.get('total_companies', 0)}")
                break
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                print(f"[WAIT] Backend not ready, waiting {retry_delay}s... (attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print("[ERROR] Backend not responding after retries")
                return False
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return False
    else:
        print("[ERROR] Backend not available")
        return False
    
    # Test export endpoint
    print("\nTesting /companies/export endpoint...")
    try:
        response = requests.get(f"{base_url}/companies/export", timeout=60)
        if response.status_code == 200:
            companies = response.json()
            print(f"[OK] Export endpoint returned {len(companies)} companies")
            
            # Check if we got all companies
            expected_count = stats.get('total_companies', 0)
            if len(companies) == expected_count:
                print(f"[SUCCESS] All {expected_count} companies exported!")
            else:
                print(f"[WARN] Expected {expected_count}, got {len(companies)}")
            
            # Validate focus_areas format
            valid_format = 0
            invalid_format = 0
            empty_format = 0
            
            for company in companies:
                focus_areas = company.get('focus_areas')
                if focus_areas is None or focus_areas == '':
                    empty_format += 1
                elif isinstance(focus_areas, list):
                    valid_format += 1
                elif isinstance(focus_areas, str):
                    try:
                        parsed = json.loads(focus_areas)
                        if isinstance(parsed, list):
                            valid_format += 1
                        else:
                            invalid_format += 1
                    except:
                        invalid_format += 1
                else:
                    invalid_format += 1
            
            print(f"\nFocus Areas Format:")
            print(f"  Valid JSON arrays: {valid_format}")
            print(f"  Invalid format: {invalid_format}")
            print(f"  Empty/null: {empty_format}")
            
            # Show sample
            if companies:
                sample = companies[0]
                print(f"\nSample company:")
                print(f"  Name: {sample.get('name')}")
                print(f"  Domain: {sample.get('domain')}")
                print(f"  Focus Areas: {sample.get('focus_areas')}")
            
            return len(companies) == expected_count
        elif response.status_code == 404:
            print("[ERROR] Export endpoint not found - backend needs restart!")
            return False
        else:
            print(f"[ERROR] Export endpoint returned status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[ERROR] Error testing export endpoint: {e}")
        return False

if __name__ == "__main__":
    success = test_export_endpoint()
    print("\n" + "="*60)
    if success:
        print("[SUCCESS] Export endpoint test passed!")
    else:
        print("[FAILED] Export endpoint test failed!")
    print("="*60)

