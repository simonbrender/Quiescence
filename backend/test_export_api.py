"""Test the companies API to see why only 12 companies are returned"""
import requests
import json

# Test regular endpoint
print("Testing /companies endpoint...")
response = requests.get('http://localhost:8000/companies', params={'limit': 100000, 'exclude_mock': False})
print(f"Status: {response.status_code}")
print(f"Count: {len(response.json())}")

# Check if there are companies with NULL scores
print("\nTesting stats...")
stats = requests.get('http://localhost:8000/stats').json()
print(f"Total companies in DB: {stats['total_companies']}")
print(f"Returned by API: {len(response.json())}")

# Check first few companies
if response.json():
    print("\nFirst company structure:")
    print(json.dumps(response.json()[0], indent=2))

