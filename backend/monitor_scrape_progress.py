"""Monitor portfolio scrape progress"""
import time
import requests
import json

def check_progress():
    """Check current scrape progress"""
    try:
        # Check database
        response = requests.get('http://localhost:8000/companies?exclude_mock=true', timeout=5)
        companies = response.json()
        
        yc_count = sum(1 for c in companies if c.get('source') in ['Y Combinator', 'yc', 'y_combinator'])
        antler_count = sum(1 for c in companies if c.get('source') in ['Antler', 'antler'])
        
        print(f"\nCurrent Progress:")
        print(f"  Total companies: {len(companies)}")
        print(f"  YC companies: {yc_count}")
        print(f"  Antler companies: {antler_count}")
        
        return len(companies), yc_count, antler_count
    except Exception as e:
        print(f"Error checking progress: {e}")
        return 0, 0, 0

if __name__ == "__main__":
    print("Monitoring portfolio scrape progress...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            total, yc, antler = check_progress()
            
            # Check if we're close to expected counts
            if antler >= 1200:
                print("\n[SUCCESS] Antler scrape appears complete!")
            if yc >= 1000:
                print("\n[SUCCESS] YC scrape appears complete!")
            
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")




