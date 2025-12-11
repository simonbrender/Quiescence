"""
Celerio Scout - Main Entry Point
Orchestrates the complete pipeline: Scrape → Enrich → Diagnose
"""
import asyncio
import json
from pathlib import Path

from scraper.scraper import PortfolioScraper
from analysis.enrichment import StallSignalEnricher, load_companies, save_enriched_companies
from analysis.diagnosis_agent import RevenueArchitectAgent, save_diagnoses


async def main():
    """
    Main pipeline execution
    """
    print("=" * 60)
    print("CELERIO SCOUT - Phase 1 Pipeline")
    print("=" * 60)
    
    # Step 1: Scrape portfolios
    print("\n[1/3] Scraping VC Portfolios...")
    scraper = PortfolioScraper(output_file="data/scout_targets.json")
    companies = await scraper.scrape_all_portfolios()
    print(f"✓ Scraped {len(companies)} companies")
    
    if not companies:
        print("⚠ No companies scraped. Using mock data for testing...")
        companies = [
            {
                'name': 'Example AI Startup',
                'description': 'AI-powered B2B solution',
                'sector': 'Enterprise AI',
                'founder_linkedin': '',
                'source': 'NFX',
                'source_url': 'https://www.nfx.com/portfolio',
                'total_funding': 8000000,
                'headcount': 45,
                'stage': 'Series A',
                'last_funding_date': '2023-06-01',
                'engineering_count': 15,
                'engineering_count_6mo_ago': 15,
                'sales_count': 6,
                'sales_count_6mo_ago': 12,
                'tech_stack': ['HubSpot', 'Salesforce'],
                'tech_stack_3mo_ago': ['HubSpot', 'Salesforce', '6sense', 'Segment'],
                'website_copy': 'We are a leading innovative cutting-edge revolutionary solution',
                'h1_tags': ['Leading AI Platform'],
                'github_stars': 50,
                'github_last_commit_days': 120
            }
        ]
        scraper.save_companies(companies)
    
    # Step 2: Enrich with OSINT signals
    print("\n[2/3] Enriching with OSINT Signals...")
    enricher = StallSignalEnricher()
    enriched_companies = enricher.enrich_batch(companies)
    save_enriched_companies(enriched_companies, "data/enriched_targets.json")
    
    # Count signals
    total_signals = sum(len(c.get('stall_signals', [])) for c in enriched_companies)
    high_risk = sum(1 for c in enriched_companies if c.get('stall_risk_score') == 'high')
    print(f"✓ Enriched {len(enriched_companies)} companies")
    print(f"  - Total stall signals detected: {total_signals}")
    print(f"  - High-risk companies: {high_risk}")
    
    # Step 3: Diagnose using 3M Framework
    print("\n[3/3] Running 3M Diagnosis...")
    agent = RevenueArchitectAgent()
    
    # Filter criteria matching user query
    filter_criteria = {
        'funding_range': (3000000, 15000000),
        'headcount_range': (10, 80),
        'months_post_raise': (12, 18),
        'stage': 'Series A'
    }
    
    diagnoses = agent.diagnose_batch(enriched_companies, filter_criteria)
    save_diagnoses(diagnoses, "data/diagnoses.json")
    
    print(f"✓ Diagnosed {len(diagnoses)} companies matching criteria")
    
    # Summary report
    print("\n" + "=" * 60)
    print("DIAGNOSIS SUMMARY")
    print("=" * 60)
    
    vector_counts = {'market': 0, 'motion': 0, 'messaging': 0, 'healthy': 0}
    for diagnosis in diagnoses:
        primary = diagnosis['primary_diagnosis']
        vector_counts[primary] = vector_counts.get(primary, 0) + 1
    
    print(f"\nPrimary Diagnoses:")
    for vector, count in vector_counts.items():
        if count > 0:
            print(f"  {vector.upper()}: {count} companies")
    
    # Show top 3 diagnoses
    print(f"\nTop Diagnoses:")
    for i, diagnosis in enumerate(diagnoses[:3], 1):
        print(f"\n{i}. {diagnosis['company_name']}")
        print(f"   Primary: {diagnosis['primary_diagnosis'].upper()}")
        if diagnosis['prescription'].get('fractional_executive'):
            print(f"   Prescription: {diagnosis['prescription']['fractional_executive']}")
    
    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)
    print("\nOutput Files:")
    print("  - data/scout_targets.json (scraped companies)")
    print("  - data/enriched_targets.json (with OSINT signals)")
    print("  - data/diagnoses.json (3M diagnoses)")


if __name__ == "__main__":
    asyncio.run(main())





