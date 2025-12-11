"""Start server and run tests"""
import subprocess
import time
import requests
import sys
import os

def start_server():
    """Start the backend server"""
    print("Starting backend server...")
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # Start server in background
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

def wait_for_server(max_wait=30):
    """Wait for server to be ready"""
    print("Waiting for server to start...")
    for i in range(max_wait):
        try:
            response = requests.get("http://localhost:8000/", timeout=2)
            if response.status_code == 200:
                print("✓ Server is ready!")
                return True
        except:
            pass
        time.sleep(1)
        if i % 5 == 0:
            print(f"  Still waiting... ({i}/{max_wait}s)")
    return False

def run_tests():
    """Run API tests"""
    print("\n" + "="*80)
    print("RUNNING API TESTS")
    print("="*80)
    
    # Test 1: GET /companies
    print("\n1. Testing GET /companies:")
    try:
        response = requests.get("http://localhost:8000/companies?limit=5", timeout=10)
        if response.status_code == 200:
            companies = response.json()
            print(f"   ✓ Found {len(companies)} companies")
            if companies:
                c = companies[0]
                print(f"   Sample: {c.get('name')} - {c.get('domain')}")
                print(f"   Scores: M={c.get('messaging_score')}, Mo={c.get('motion_score')}, Ma={c.get('market_score')}")
        else:
            print(f"   ✗ Error: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: POST /companies/search
    print("\n2. Testing POST /companies/search (Series A):")
    try:
        response = requests.post(
            "http://localhost:8000/companies/search",
            json={"stages": ["Series A"]},
            timeout=15
        )
        if response.status_code == 200:
            companies = response.json()
            print(f"   ✓ Found {len(companies)} companies")
        else:
            print(f"   ✗ Error: {response.status_code} - {response.text[:500]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: POST /companies/search with focus_areas
    print("\n3. Testing POST /companies/search (AI/ML focus):")
    try:
        response = requests.post(
            "http://localhost:8000/companies/search",
            json={"focus_areas": ["AI/ML"]},
            timeout=15
        )
        if response.status_code == 200:
            companies = response.json()
            print(f"   ✓ Found {len(companies)} companies")
        else:
            print(f"   ✗ Error: {response.status_code} - {response.text[:500]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    process = None
    try:
        process = start_server()
        if wait_for_server():
            run_tests()
        else:
            print("✗ Server failed to start")
            if process:
                stdout, stderr = process.communicate(timeout=5)
                print("STDOUT:", stdout)
                print("STDERR:", stderr)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if process:
            process.terminate()
            process.wait()




