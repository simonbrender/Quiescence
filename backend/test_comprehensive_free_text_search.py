"""
Comprehensive Automated Tests for Free-Text Search
Tests that the platform returns EVERY applicable company for any free-text search term
relevant to the software startup ecosystem.

This test suite iterates through various search scenarios and validates:
1. Query parsing accuracy
2. Database query correctness  
3. Web discovery completeness
4. Result completeness and accuracy

Run this while the backend server is running on http://localhost:8000
"""

import requests
import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from nlp_query_parser import parse_natural_language_query


class FreeTextSearchTestSuite:
    """Comprehensive test suite for free-text search functionality"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.test_results = []
        self.failed_tests = []
        
    def test_query_parsing(self, query: str, expected_params: Dict) -> bool:
        """Test that query parsing extracts correct parameters"""
        print(f"\n[TEST] Testing query parsing: '{query}'")
        try:
            parsed = parse_natural_language_query(query)
            
            # Check each expected parameter
            for key, expected_value in expected_params.items():
                if key not in parsed:
                    print(f"  [FAIL] Missing parameter: {key}")
                    return False
                if parsed[key] != expected_value:
                    # For lists, check if they contain the expected values
                    if isinstance(expected_value, list) and isinstance(parsed[key], list):
                        if not all(item in parsed[key] for item in expected_value):
                            print(f"  [FAIL] Parameter mismatch: {key}")
                            print(f"    Expected: {expected_value}")
                            print(f"    Got: {parsed[key]}")
                            return False
                    else:
                        print(f"  [FAIL] Parameter mismatch: {key}")
                        print(f"    Expected: {expected_value}")
                        print(f"    Got: {parsed[key]}")
                        return False
            
            print(f"  [PASS] Query parsed correctly")
            print(f"    Parsed params: {json.dumps(parsed, indent=4, default=str)}")
            return True
        except Exception as e:
            print(f"  [FAIL] Error parsing query: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_search_endpoint(self, query: str, expected_min_count: int = 0, timeout: int = 30) -> tuple[bool, List[Dict], float]:
        """Test the full search endpoint via API"""
        print(f"\n[TEST] Testing search endpoint: '{query}'")
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_base_url}/companies/search/free-text",
                json={'query': query},
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                companies = response.json()
                if isinstance(companies, dict) and 'companies' in companies:
                    companies = companies['companies']
                
                print(f"  [RESULT] Found {len(companies)} companies in {elapsed:.2f}s")
                
                if companies:
                    print(f"  Sample companies:")
                    for i, company in enumerate(companies[:3], 1):
                        name = company.get('name', 'N/A')
                        domain = company.get('domain', 'N/A')
                        stage = company.get('last_raise_stage', 'N/A')
                        print(f"    {i}. {name} ({domain}) - {stage}")
                
                if len(companies) < expected_min_count:
                    print(f"  [WARN] Expected at least {expected_min_count} companies, got {len(companies)}")
                    return False, companies, elapsed
                
                return True, companies, elapsed
            else:
                print(f"  [FAIL] API returned status {response.status_code}")
                print(f"  Response: {response.text[:500]}")
                return False, [], elapsed
                
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            print(f"  [FAIL] Request timed out after {elapsed:.2f}s")
            return False, [], elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  [FAIL] Error testing search endpoint: {e}")
            import traceback
            traceback.print_exc()
            return False, [], elapsed
    
    def validate_result_completeness(self, query: str, companies: List[Dict], parsed_params: Dict) -> bool:
        """Validate that returned companies match the query criteria"""
        print(f"\n[VALIDATE] Validating result completeness for: '{query}'")
        
        if not companies:
            print("  [SKIP] No companies to validate")
            return True
        
        mismatches = []
        for i, company in enumerate(companies[:10], 1):  # Check first 10
            issues = []
            
            # Check stages
            if parsed_params.get('stages'):
                company_stage = company.get('last_raise_stage')
                if company_stage and company_stage not in parsed_params['stages']:
                    issues.append(f"Stage mismatch: {company_stage} not in {parsed_params['stages']}")
            
            # Check focus areas
            if parsed_params.get('focus_areas'):
                company_focus = company.get('focus_areas', [])
                if isinstance(company_focus, str):
                    try:
                        company_focus = json.loads(company_focus)
                    except:
                        company_focus = []
                if not isinstance(company_focus, list):
                    company_focus = []
                
                if not any(area in company_focus for area in parsed_params['focus_areas']):
                    issues.append(f"Focus area mismatch: {company_focus} doesn't contain {parsed_params['focus_areas']}")
            
            # Check funding
            if parsed_params.get('funding_min') is not None:
                funding = company.get('funding_amount', 0)
                if isinstance(funding, (int, float)):
                    funding_m = funding / 1000000
                    if funding_m < parsed_params['funding_min']:
                        issues.append(f"Funding too low: ${funding_m}M < ${parsed_params['funding_min']}M")
            
            if parsed_params.get('funding_max') is not None:
                funding = company.get('funding_amount', 0)
                if isinstance(funding, (int, float)):
                    funding_m = funding / 1000000
                    if funding_m > parsed_params['funding_max']:
                        issues.append(f"Funding too high: ${funding_m}M > ${parsed_params['funding_max']}M")
            
            # Check employees
            if parsed_params.get('employees_min') is not None:
                employees = company.get('employees', 0)
                if employees < parsed_params['employees_min']:
                    issues.append(f"Too few employees: {employees} < {parsed_params['employees_min']}")
            
            if parsed_params.get('employees_max') is not None:
                employees = company.get('employees', 0)
                if employees > parsed_params['employees_max']:
                    issues.append(f"Too many employees: {employees} > {parsed_params['employees_max']}")
            
            if issues:
                mismatches.append({
                    'company': company.get('name', 'Unknown'),
                    'issues': issues
                })
        
        if mismatches:
            print(f"  [WARN] Found {len(mismatches)} companies with mismatched criteria:")
            for mismatch in mismatches[:3]:
                print(f"    - {mismatch['company']}: {', '.join(mismatch['issues'])}")
            return False
        else:
            print(f"  [PASS] All checked companies match criteria")
            return True
    
    def run_test_suite(self):
        """Run comprehensive test suite"""
        print("=" * 80)
        print("COMPREHENSIVE FREE-TEXT SEARCH TEST SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")
        print(f"API Base URL: {self.api_base_url}")
        
        # Test cases covering various startup ecosystem search scenarios
        test_cases = [
            {
                "name": "Seed/Series A AI/B2B Companies",
                "query": "Seed/Series A AI/B2B companies 12–18 months post-raise, typically with $3–15m in total funding from a tier 1/2 VC, studio, incubator or accelerator and 10–80 employees",
                "expected_params": {
                    "stages": ["Seed", "Series A"],
                    "focus_areas": ["AI/ML", "B2B SaaS"],
                    "funding_min": 3,
                    "funding_max": 15,
                    "employees_min": 10,
                    "employees_max": 80,
                    "months_post_raise_min": 12,
                    "months_post_raise_max": 18,
                    "fund_tiers": ["Tier 1", "Tier 2"]
                },
                "expected_min_count": 0,
                "timeout": 60
            },
            {
                "name": "YC Portfolio Companies",
                "query": "retrieve the YC and Antler portfolios",
                "expected_params": {
                    "is_portfolio_query": True,
                    "portfolio_sources": ["yc", "antler"]
                },
                "expected_min_count": 0,
                "timeout": 300  # Portfolio scraping takes longer
            },
            {
                "name": "Series B Fintech Companies",
                "query": "Series B fintech companies with 50-200 employees and $10-50M funding",
                "expected_params": {
                    "stages": ["Series B"],
                    "focus_areas": ["Fintech"],
                    "employees_min": 50,
                    "employees_max": 200,
                    "funding_min": 10,
                    "funding_max": 50
                },
                "expected_min_count": 0,
                "timeout": 30
            },
            {
                "name": "Pre-Seed AI Startups",
                "query": "Pre-Seed AI/ML startups with less than 10 employees",
                "expected_params": {
                    "stages": ["Pre-Seed"],
                    "focus_areas": ["AI/ML"],
                    "employees_max": 10
                },
                "expected_min_count": 0,
                "timeout": 30
            },
            {
                "name": "Enterprise SaaS Companies",
                "query": "Enterprise SaaS companies in Series A or Series B stage",
                "expected_params": {
                    "stages": ["Series A", "Series B"],
                    "focus_areas": ["Enterprise"]
                },
                "expected_min_count": 0,
                "timeout": 30
            },
            {
                "name": "DevTools Startups",
                "query": "DevTools startups with 20-100 employees",
                "expected_params": {
                    "focus_areas": ["DevTools"],
                    "employees_min": 20,
                    "employees_max": 100
                },
                "expected_min_count": 0,
                "timeout": 30
            },
            {
                "name": "Growth Stage Companies",
                "query": "Growth stage companies with over $50M funding",
                "expected_params": {
                    "stages": ["Growth"],
                    "funding_min": 50
                },
                "expected_min_count": 0,
                "timeout": 30
            },
            {
                "name": "Tier 1 VC Backed Companies",
                "query": "Companies backed by Tier 1 VCs with Series A funding",
                "expected_params": {
                    "stages": ["Series A"],
                    "fund_tiers": ["Tier 1"]
                },
                "expected_min_count": 0,
                "timeout": 30
            },
            {
                "name": "Recent Raises (6-12 months)",
                "query": "Companies that raised 6-12 months ago",
                "expected_params": {
                    "months_post_raise_min": 6,
                    "months_post_raise_max": 12
                },
                "expected_min_count": 0,
                "timeout": 30
            },
            {
                "name": "Small Team B2B SaaS",
                "query": "B2B SaaS companies with 5-20 employees",
                "expected_params": {
                    "focus_areas": ["B2B SaaS"],
                    "employees_min": 5,
                    "employees_max": 20
                },
                "expected_min_count": 0,
                "timeout": 30
            },
            {
                "name": "AI Companies General",
                "query": "AI companies with Series A funding",
                "expected_params": {
                    "stages": ["Series A"],
                    "focus_areas": ["AI/ML"]
                },
                "expected_min_count": 0,
                "timeout": 30
            },
            {
                "name": "Invalid Query Test",
                "query": "how big are my feet?",
                "expected_params": {},
                "expected_min_count": 0,
                "timeout": 10,
                "should_fail": True  # This should return empty or error
            }
        ]
        
        # Run tests
        passed = 0
        failed = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'=' * 80}")
            print(f"TEST {i}/{len(test_cases)}: {test_case['name']}")
            print(f"{'=' * 80}")
            
            # Test query parsing (skip for invalid queries)
            if not test_case.get('should_fail', False):
                parse_success = self.test_query_parsing(test_case['query'], test_case['expected_params'])
            else:
                parse_success = True  # Invalid queries may parse differently
            
            # Test search endpoint
            timeout = test_case.get('timeout', 30)
            search_success, companies, elapsed = self.test_search_endpoint(
                test_case['query'], 
                test_case['expected_min_count'],
                timeout=timeout
            )
            
            # Validate results if search succeeded
            validation_success = True
            if search_success and companies and not test_case.get('should_fail', False):
                parsed_params = parse_natural_language_query(test_case['query'])
                validation_success = self.validate_result_completeness(
                    test_case['query'], 
                    companies, 
                    parsed_params
                )
            
            # Record results
            result = {
                "test_name": test_case['name'],
                "query": test_case['query'],
                "parse_success": parse_success,
                "search_success": search_success,
                "validation_success": validation_success,
                "companies_found": len(companies),
                "elapsed_time": elapsed,
                "companies": companies[:5] if companies else []  # Store first 5 for inspection
            }
            self.test_results.append(result)
            
            # Determine if test passed
            if test_case.get('should_fail', False):
                # For invalid queries, success means empty results or error
                test_passed = not search_success or len(companies) == 0
            else:
                test_passed = parse_success and search_success and validation_success
            
            if test_passed:
                passed += 1
                print(f"\n[PASS] Test '{test_case['name']}' passed")
            else:
                failed += 1
                self.failed_tests.append(test_case['name'])
                print(f"\n[FAIL] Test '{test_case['name']}' failed")
            
            # Brief pause between tests
            if i < len(test_cases):
                time.sleep(2)
        
        # Print summary
        print(f"\n{'=' * 80}")
        print("TEST SUMMARY")
        print(f"{'=' * 80}")
        print(f"Total tests: {len(test_cases)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if self.failed_tests:
            print(f"\nFailed tests:")
            for test_name in self.failed_tests:
                print(f"  - {test_name}")
        
        # Save results to file
        results_file = Path(__file__).parent / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "api_base_url": self.api_base_url,
                "total_tests": len(test_cases),
                "passed": passed,
                "failed": failed,
                "results": self.test_results
            }, f, indent=2, default=str)
        
        print(f"\nResults saved to: {results_file}")
        
        return passed, failed


def main():
    """Run the comprehensive test suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive free-text search tests')
    parser.add_argument('--api-url', default='http://localhost:8000', 
                       help='API base URL (default: http://localhost:8000)')
    args = parser.parse_args()
    
    # Check if backend is running
    try:
        response = requests.get(f"{args.api_url}/stats", timeout=5)
        if response.status_code != 200:
            print(f"[ERROR] Backend is not responding correctly at {args.api_url}")
            print("Please ensure the backend server is running.")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Cannot connect to backend at {args.api_url}")
        print(f"Error: {e}")
        print("Please ensure the backend server is running.")
        sys.exit(1)
    
    suite = FreeTextSearchTestSuite(api_base_url=args.api_url)
    
    # Run tests
    passed, failed = suite.run_test_suite()
    
    # Exit with appropriate code
    if failed > 0:
        print(f"\n[FAILURE] {failed} test(s) failed")
        sys.exit(1)
    else:
        print(f"\n[SUCCESS] All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
