"""
Validate API Results - Test all endpoints and show real data
"""
import requests
import json
from typing import Dict, List

API_BASE = "http://localhost:8000"

def test_endpoint(endpoint: str, method: str = "GET", data: dict = None) -> Dict:
    """Test an API endpoint"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json(), "status": response.status_code}
        else:
            return {"success": False, "error": response.text, "status": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e), "status": None}

def main():
    print("\n" + "="*80)
    print("API VALIDATION - REAL RESULTS")
    print("="*80 + "\n")
    
    results = {}
    
    # Test 1: Get Investors
    print("1. Testing GET /investors...")
    investors_result = test_endpoint("/investors")
    results["investors"] = investors_result
    if investors_result["success"]:
        investors = investors_result["data"]
        print(f"   SUCCESS: Found {len(investors)} investors")
        if len(investors) > 0:
            print(f"   Sample: {investors[0].get('firm_name', 'N/A')}")
    else:
        print(f"   FAILED: {investors_result.get('error', 'Unknown error')}")
    
    # Test 2: Get Investor Relationships
    print("\n2. Testing GET /investors/relationships...")
    relationships_result = test_endpoint("/investors/relationships")
    results["relationships"] = relationships_result
    if relationships_result["success"]:
        relationships = relationships_result["data"]
        print(f"   SUCCESS: Found {len(relationships)} relationships")
        if len(relationships) > 0:
            rel = relationships[0]
            print(f"   Sample: Investor {rel.get('investor_id')} -> Company {rel.get('company_id')}")
    else:
        print(f"   FAILED: {relationships_result.get('error', 'Unknown error')}")
    
    # Test 3: Get Companies
    print("\n3. Testing GET /companies...")
    companies_result = test_endpoint("/companies?limit=10")
    results["companies"] = companies_result
    if companies_result["success"]:
        companies = companies_result["data"]
        print(f"   SUCCESS: Found {len(companies)} companies (limited to 10)")
        if len(companies) > 0:
            print(f"   Sample: {companies[0].get('name', 'N/A')} ({companies[0].get('domain', 'N/A')})")
    else:
        print(f"   FAILED: {companies_result.get('error', 'Unknown error')}")
    
    # Test 4: Get Stats
    print("\n4. Testing GET /stats...")
    stats_result = test_endpoint("/stats")
    results["stats"] = stats_result
    if stats_result["success"]:
        stats = stats_result["data"]
        print(f"   SUCCESS: Got stats")
        print(f"   Total Companies: {stats.get('total_companies', 'N/A')}")
        print(f"   Total VCs: {stats.get('total_vcs', 'N/A')}")
    else:
        print(f"   FAILED: {stats_result.get('error', 'Unknown error')}")
    
    # Test 5: Get Companies Export
    print("\n5. Testing GET /companies/export...")
    export_result = test_endpoint("/companies/export")
    results["export"] = export_result
    if export_result["success"]:
        export_data = export_result["data"]
        print(f"   SUCCESS: Export endpoint working")
        print(f"   Companies in export: {len(export_data)}")
        if len(export_data) > 0:
            print(f"   Sample: {export_data[0].get('name', 'N/A')}")
    else:
        print(f"   FAILED: {export_result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r.get("success"))
    total = len(results)
    
    print(f"\nEndpoints Tested: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\nVALIDATION: ALL TESTS PASSED")
    else:
        print("\nVALIDATION: SOME TESTS FAILED")
        for name, result in results.items():
            if not result.get("success"):
                print(f"  - {name}: {result.get('error', 'Unknown error')}")
    
    # Show actual data counts
    print("\n" + "-"*80)
    print("DATA COUNTS")
    print("-"*80)
    
    if results["investors"]["success"]:
        print(f"Investors: {len(results['investors']['data'])}")
    if results["relationships"]["success"]:
        print(f"Relationships: {len(results['relationships']['data'])}")
    if results["companies"]["success"]:
        print(f"Companies (sample): {len(results['companies']['data'])}")
    if results["export"]["success"]:
        print(f"Companies (export): {len(results['export']['data'])}")
    if results["stats"]["success"]:
        stats = results["stats"]["data"]
        print(f"Total Companies (stats): {stats.get('total_companies', 'N/A')}")
        print(f"Total VCs (stats): {stats.get('total_vcs', 'N/A')}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

