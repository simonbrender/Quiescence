"""
API-Based Portfolio Scraping Monitor
Shows real-time metrics via API (doesn't require direct DB access)
"""
import requests
import time
from datetime import datetime
from typing import Dict

def get_stats_via_api() -> Dict:
    """Get statistics via API"""
    stats = {}
    
    try:
        # Get all companies
        response = requests.get("http://localhost:8000/companies?limit=10000", timeout=10)
        if response.status_code == 200:
            companies = response.json()
            stats['total'] = len(companies)
            
            # Calculate metrics
            stats['by_source'] = {}
            stats['yc_companies'] = 0
            stats['antler_companies'] = 0
            
            stats['with_name'] = 0
            stats['with_domain'] = 0
            stats['with_stage'] = 0
            stats['with_focus'] = 0
            stats['with_employees'] = 0
            stats['with_funding'] = 0
            
            stats['recent_companies'] = []
            
            for company in companies:
                # Count by source
                source = company.get('source', 'unknown')
                stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
                
                # Count YC/Antler
                if 'yc' in source.lower() or company.get('yc_batch'):
                    stats['yc_companies'] += 1
                if 'antler' in source.lower():
                    stats['antler_companies'] += 1
                
                # Count completeness
                if company.get('name'):
                    stats['with_name'] += 1
                if company.get('domain'):
                    stats['with_domain'] += 1
                if company.get('last_raise_stage'):
                    stats['with_stage'] += 1
                if company.get('focus_areas'):
                    stats['with_focus'] += 1
                if company.get('employee_count'):
                    stats['with_employees'] += 1
                if company.get('funding_amount'):
                    stats['with_funding'] += 1
            
            # Get recent companies (last 10)
            stats['recent_companies'] = sorted(
                companies, 
                key=lambda x: x.get('created_at', ''), 
                reverse=True
            )[:10]
            
            # Calculate percentages
            total = stats['total']
            if total > 0:
                stats['name_pct'] = (stats['with_name'] / total) * 100
                stats['domain_pct'] = (stats['with_domain'] / total) * 100
                stats['stage_pct'] = (stats['with_stage'] / total) * 100
                stats['focus_pct'] = (stats['with_focus'] / total) * 100
                stats['employees_pct'] = (stats['with_employees'] / total) * 100
                stats['funding_pct'] = (stats['with_funding'] / total) * 100
            else:
                stats['name_pct'] = 0
                stats['domain_pct'] = 0
                stats['stage_pct'] = 0
                stats['focus_pct'] = 0
                stats['employees_pct'] = 0
                stats['funding_pct'] = 0
            
        else:
            stats['error'] = f"API returned {response.status_code}"
    except Exception as e:
        stats['error'] = str(e)
    
    return stats

def print_metrics(stats: Dict, iteration: int, start_time: float, last_total: int = 0):
    """Print formatted metrics"""
    elapsed = time.time() - start_time
    elapsed_min = elapsed / 60
    
    print("\n" + "=" * 100)
    print(f"PORTFOLIO SCRAPING MONITOR (API-Based) - Iteration #{iteration} - Elapsed: {elapsed_min:.1f} minutes")
    print("=" * 100)
    
    if 'error' in stats:
        print(f"\n[ERROR] {stats['error']}")
        return
    
    # Overall stats
    print(f"\n[TOTAL COMPANIES] {stats['total']}")
    print(f"  YC Companies: {stats['yc_companies']}")
    print(f"  Antler Companies: {stats['antler_companies']}")
    
    # Show change
    if iteration > 1 and last_total > 0:
        new_companies = stats['total'] - last_total
        if new_companies > 0:
            print(f"  [+{new_companies} NEW since last check]")
        elif new_companies < 0:
            print(f"  [{new_companies} removed since last check]")
    
    # By source breakdown
    if stats.get('by_source'):
        print(f"\n[BY SOURCE]")
        for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")
    
    # Ingestion rate
    if elapsed_min > 0:
        rate = stats['total'] / elapsed_min
        print(f"\n[INGESTION RATE]")
        print(f"  Average rate: {rate:.2f} companies/minute")
        if stats['total'] > 0:
            print(f"  Estimated time to 1,000 companies: {(1000 - stats['total']) / rate:.1f} minutes")
            print(f"  Estimated time to 5,000 companies: {(5000 - stats['total']) / rate:.1f} minutes")
    
    # Data quality metrics
    print(f"\n[DATA QUALITY METRICS]")
    print(f"  Name: {stats['with_name']}/{stats['total']} ({stats['name_pct']:.1f}%)")
    print(f"  Domain: {stats['with_domain']}/{stats['total']} ({stats['domain_pct']:.1f}%)")
    print(f"  Stage: {stats['with_stage']}/{stats['total']} ({stats['stage_pct']:.1f}%)")
    print(f"  Focus Areas: {stats['with_focus']}/{stats['total']} ({stats['focus_pct']:.1f}%)")
    print(f"  Employees: {stats['with_employees']}/{stats['total']} ({stats['employees_pct']:.1f}%)")
    print(f"  Funding: {stats['with_funding']}/{stats['total']} ({stats['funding_pct']:.1f}%)")
    
    # Overall quality score
    quality_score = (
        stats['name_pct'] + stats['domain_pct'] + stats['stage_pct'] + 
        stats['focus_pct'] + stats['employees_pct'] + stats['funding_pct']
    ) / 6
    print(f"\n  [OVERALL QUALITY SCORE] {quality_score:.1f}%")
    
    if quality_score >= 80:
        print(f"  Status: EXCELLENT (Enterprise-grade)")
    elif quality_score >= 60:
        print(f"  Status: GOOD")
    elif quality_score >= 40:
        print(f"  Status: FAIR")
    else:
        print(f"  Status: NEEDS IMPROVEMENT")
    
    # Recent companies
    if stats.get('recent_companies'):
        print(f"\n[RECENTLY ADDED COMPANIES] (Last 10)")
        for i, company in enumerate(stats['recent_companies'][:10], 1):
            name = company.get('name', 'N/A')
            domain = company.get('domain', 'N/A')
            source = company.get('source', 'N/A')
            stage = company.get('last_raise_stage', 'N/A')
            focus = company.get('focus_areas', [])
            if isinstance(focus, str):
                focus_str = focus[:50]
            elif isinstance(focus, list):
                focus_str = ', '.join(focus[:2])[:50]
            else:
                focus_str = 'None'
            
            print(f"  {i}. {name} ({domain})")
            print(f"     Source: {source}, Stage: {stage}, Focus: {focus_str}")
    
    print("\n" + "=" * 100)

def main():
    """Main monitoring loop"""
    print("=" * 100)
    print("PORTFOLIO SCRAPING CONTINUOUS MONITOR (API-Based)")
    print("=" * 100)
    print(f"API: http://localhost:8000")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nMonitoring every 10 seconds...")
    print("Press Ctrl+C to stop")
    
    start_time = time.time()
    iteration = 0
    last_total = 0
    
    try:
        while True:
            iteration += 1
            stats = get_stats_via_api()
            
            # Show metrics
            print_metrics(stats, iteration, start_time, last_total)
            
            if 'total' in stats:
                last_total = stats['total']
            
            # Wait before next check
            print(f"\nNext check in 10 seconds... (Ctrl+C to stop)")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 100)
        print("MONITORING STOPPED")
        print("=" * 100)
        final_stats = get_stats_via_api()
        if 'error' not in final_stats:
            print_metrics(final_stats, iteration, start_time, last_total)
            print("\nFinal Summary:")
            print(f"  Total companies: {final_stats['total']}")
            print(f"  YC: {final_stats['yc_companies']}")
            print(f"  Antler: {final_stats['antler_companies']}")
            quality_score = (
                final_stats['name_pct'] + final_stats['domain_pct'] + final_stats['stage_pct'] + 
                final_stats['focus_pct'] + final_stats['employees_pct'] + final_stats['funding_pct']
            ) / 6
            print(f"  Quality Score: {quality_score:.1f}%")

if __name__ == "__main__":
    main()






