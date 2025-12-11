"""
Trigger comprehensive portfolio scraping for YC and Antler
This will scrape ALL companies from both portfolios
"""
import asyncio
import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def trigger_portfolio_scraping():
    """Trigger portfolio scraping via API"""
    print("=" * 80)
    print("TRIGGERING PORTFOLIO SCRAPING")
    print("=" * 80)
    
    # Trigger via free-text search endpoint
    query = "retrieve the YC and Antler portfolios"
    
    print(f"\nSending portfolio scraping request...")
    print(f"Query: {query}")
    
    try:
        response = requests.post(
            "http://localhost:8000/companies/search/free-text",
            json={'query': query},
            timeout=10,  # Short timeout - scraping happens in background
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            session_id = response.headers.get('X-Session-ID')
            print(f"\n✅ Portfolio scraping started!")
            print(f"Session ID: {session_id}")
            print(f"\nScraping is running in the background.")
            print(f"Companies will be added to the database as they're discovered.")
            print(f"\nMonitor progress via WebSocket: ws://localhost:8000/api/ws/portfolio-scraping/{session_id}")
            print(f"\nOr check database periodically for new companies.")
            return session_id
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
    except Exception as e:
        print(f"❌ Error triggering scraping: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    session_id = asyncio.run(trigger_portfolio_scraping())
    if session_id:
        print(f"\n✅ Scraping initiated successfully!")
        print(f"Check the database in a few minutes for results.")
    else:
        print(f"\n❌ Failed to initiate scraping")

