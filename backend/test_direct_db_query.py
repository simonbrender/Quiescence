"""Test database queries via API to understand data format"""
import requests
import json

print("=" * 80)
print("DIRECT DATABASE QUERY TEST VIA API")
print("=" * 80)

# Test 1: Get all companies (no filters)
print("\n1. Testing GET /companies (no filters):")
try:
    response = requests.get("http://localhost:8000/companies?limit=5", timeout=10)
    if response.status_code == 200:
        companies = response.json()
        print(f"   Found {len(companies)} companies")
        if companies:
            print("   Sample company:")
            c = companies[0]
            print(f"     Name: {c.get('name')}")
            print(f"     Domain: {c.get('domain')}")
            print(f"     Stage: {c.get('last_raise_stage')}")
            print(f"     Focus Areas: {c.get('focus_areas')} (type: {type(c.get('focus_areas'))})")
            print(f"     Source: {c.get('source')}")
            print(f"     Employees: {c.get('employee_count')} or {c.get('employees')}")
    else:
        print(f"   Error: {response.status_code} - {response.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Advanced search with Series A
print("\n2. Testing POST /companies/search (Series A):")
try:
    response = requests.post(
        "http://localhost:8000/companies/search",
        json={"stages": ["Series A"]},
        timeout=15
    )
    if response.status_code == 200:
        companies = response.json()
        print(f"   Found {len(companies)} companies")
        if companies:
            print("   Sample companies:")
            for i, c in enumerate(companies[:3], 1):
                print(f"     {i}. {c.get('name')} - Stage: {c.get('last_raise_stage')}")
    else:
        print(f"   Error: {response.status_code} - {response.text[:500]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Advanced search with focus areas
print("\n3. Testing POST /companies/search (AI/ML focus):")
try:
    response = requests.post(
        "http://localhost:8000/companies/search",
        json={"focus_areas": ["AI/ML"]},
        timeout=15
    )
    if response.status_code == 200:
        companies = response.json()
        print(f"   Found {len(companies)} companies")
        if companies:
            print("   Sample companies:")
            for i, c in enumerate(companies[:3], 1):
                print(f"     {i}. {c.get('name')} - Focus: {c.get('focus_areas')}")
    else:
        print(f"   Error: {response.status_code} - {response.text[:500]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 4: Free text search
print("\n4. Testing POST /companies/search/free-text ('Series A companies'):")
try:
    response = requests.post(
        "http://localhost:8000/companies/search/free-text",
        json={"query": "Series A companies"},
        timeout=15
    )
    if response.status_code == 200:
        companies = response.json()
        print(f"   Found {len(companies)} companies")
        if companies:
            print("   Sample companies:")
            for i, c in enumerate(companies[:3], 1):
                print(f"     {i}. {c.get('name')} - Stage: {c.get('last_raise_stage')}")
    else:
        print(f"   Error: {response.status_code} - {response.text[:500]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 80)

