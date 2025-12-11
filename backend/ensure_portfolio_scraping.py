"""
Ensure portfolio scraping is running continuously
Triggers scraping if not already running
"""
import asyncio
import requests
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def trigger_scraping():
    """Trigger portfolio scraping via API"""
    try:
        response = requests.post(
            "http://localhost:8000/companies/search/free-text",
            json={'query': 'retrieve the YC and Antler portfolios'},
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            session_id = response.headers.get('X-Session-ID')
            print(f"[SUCCESS] Portfolio scraping triggered!")
            print(f"Session ID: {session_id}")
            return session_id
        else:
            print(f"[ERROR] Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Failed to trigger: {e}")
        return None

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/stats", timeout=3)
        return response.status_code == 200
    except:
        return False

def main():
    """Ensure scraping is running"""
    print("=" * 80)
    print("ENSURING PORTFOLIO SCRAPING IS RUNNING")
    print("=" * 80)
    
    if not check_backend():
        print("[ERROR] Backend is not running!")
        print("Please start the backend server first:")
        print("  cd backend && python main.py")
        return
    
    print("[OK] Backend is running")
    
    # Trigger scraping
    session_id = trigger_scraping()
    
    if session_id:
        print(f"\n[SUCCESS] Scraping initiated!")
        print(f"Monitor progress with: python monitor_portfolio_scraping.py")
    else:
        print(f"\n[ERROR] Failed to initiate scraping")

if __name__ == "__main__":
    main()




