"""Test the improved rule-based parser"""
import sys
import json
from nlp_query_parser import rule_based_parse

test_cases = [
    "Seed/Series A AI/B2B companies 12–18 months post-raise, typically with $3–15m in total funding from a tier 1/2 VC, studio, incubator or accelerator and 10–80 employees",
    "Series B fintech companies with 50-200 employees and $10-50M funding",
    "Pre-Seed AI/ML startups with less than 10 employees",
    "Companies that raised 6-12 months ago",
    "Growth stage companies with over $50M funding",
    "B2B SaaS companies with 5-20 employees"
]

print("=" * 80)
print("TESTING IMPROVED RULE-BASED PARSER")
print("=" * 80)

for i, query in enumerate(test_cases, 1):
    print(f"\nTest {i}: {query[:60]}...")
    result = rule_based_parse(query)
    print(json.dumps(result, indent=2, default=str))




