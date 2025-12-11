"""Test script for free-text search with web discovery"""
import requests
import json
import time

def test_free_text_search(query):
    """Test free-text search endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing Query: {query}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://localhost:8000/companies/search/free-text',
            json={'query': query},
            timeout=90  # Longer timeout for web discovery
        )
        
        elapsed = time.time() - start_time
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time elapsed: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            companies = response.json()
            print(f"\n[OK] Found {len(companies)} companies")
            
            if companies:
                print("\nFirst 5 companies:")
                for i, company in enumerate(companies[:5], 1):
                    print(f"  {i}. {company.get('name', 'N/A')} ({company.get('domain', 'N/A')})")
                    print(f"     Source: {company.get('source', 'N/A')}")
                    if company.get('last_raise_stage'):
                        print(f"     Stage: {company.get('last_raise_stage')}")
                    if company.get('focus_areas'):
                        print(f"     Focus: {company.get('focus_areas')}")
        else:
            print(f"\n[ERROR] {response.text[:500]}")
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n[EXCEPTION] After {elapsed:.2f} seconds: {e}")

if __name__ == "__main__":
    # Test queries
    queries = [
        "AI companies with Series A funding",
        "Seed/Series A AI/B2B companies 12–18 months post-raise, typically with $3–15m in total funding from a Tier1/2 fund and 10–80 employees",
        "Series-B startups experiencing a sudden spike in new hires in their sales team, headquartered on the East Coast US and UAE"
    ]
    
    for query in queries:
        test_free_text_search(query)
        time.sleep(2)  # Brief pause between tests

