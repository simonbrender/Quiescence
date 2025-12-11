"""
Continuous Portfolio Scraping Monitor
Shows real-time metrics proving quality data ingestion
"""
import sys
import time
import duckdb
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import json

sys.path.insert(0, str(Path(__file__).parent))

def get_database_stats(conn) -> Dict:
    """Get comprehensive database statistics"""
    stats = {}
    
    # Total companies
    stats['total'] = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    
    # Companies by source
    sources = conn.execute("SELECT source, COUNT(*) as cnt FROM companies GROUP BY source ORDER BY cnt DESC").fetchall()
    stats['by_source'] = {s[0]: s[1] for s in sources}
    
    # YC companies
    yc_count = conn.execute("""
        SELECT COUNT(*) FROM companies 
        WHERE source LIKE '%yc%' OR source LIKE '%Y Combinator%' OR yc_batch IS NOT NULL
    """).fetchone()[0]
    stats['yc_companies'] = yc_count
    
    # Antler companies
    antler_count = conn.execute("""
        SELECT COUNT(*) FROM companies 
        WHERE source LIKE '%antler%' OR source LIKE '%Antler%'
    """).fetchone()[0]
    stats['antler_companies'] = antler_count
    
    # Data completeness
    completeness = conn.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(last_raise_stage) as with_stage,
            COUNT(CASE WHEN focus_areas IS NOT NULL AND focus_areas != '' AND focus_areas != '[]' THEN 1 END) as with_focus,
            COUNT(employee_count) as with_employees,
            COUNT(funding_amount) as with_funding,
            COUNT(domain) as with_domain,
            COUNT(name) as with_name
        FROM companies
    """).fetchone()
    
    total, stage, focus, emp, fund, domain, name = completeness
    stats['completeness'] = {
        'total': total,
        'with_name': name,
        'with_domain': domain,
        'with_stage': stage,
        'with_focus_areas': focus,
        'with_employees': emp,
        'with_funding': fund,
        'name_pct': (name / total * 100) if total > 0 else 0,
        'domain_pct': (domain / total * 100) if total > 0 else 0,
        'stage_pct': (stage / total * 100) if total > 0 else 0,
        'focus_pct': (focus / total * 100) if total > 0 else 0,
        'employees_pct': (emp / total * 100) if total > 0 else 0,
        'funding_pct': (fund / total * 100) if total > 0 else 0,
    }
    
    # Recent companies (last 10)
    recent = conn.execute("""
        SELECT name, domain, source, yc_batch, created_at, last_raise_stage, focus_areas
        FROM companies
        ORDER BY created_at DESC
        LIMIT 10
    """).fetchall()
    
    stats['recent_companies'] = []
    for row in recent:
        name, domain, source, yc_batch, created_at, stage, focus = row
        stats['recent_companies'].append({
            'name': name,
            'domain': domain,
            'source': source,
            'yc_batch': yc_batch,
            'created_at': str(created_at) if created_at else None,
            'stage': stage,
            'focus_areas': focus
        })
    
    # Companies added in last minute
    one_min_ago = datetime.now().timestamp() - 60
    recent_count = conn.execute("""
        SELECT COUNT(*) FROM companies 
        WHERE created_at > datetime('now', '-1 minute')
    """).fetchone()[0]
    stats['added_last_minute'] = recent_count
    
    # Companies added in last 5 minutes
    recent_5min = conn.execute("""
        SELECT COUNT(*) FROM companies 
        WHERE created_at > datetime('now', '-5 minutes')
    """).fetchone()[0]
    stats['added_last_5min'] = recent_5min
    
    return stats

def print_metrics(stats: Dict, iteration: int, start_time: float):
    """Print formatted metrics"""
    elapsed = time.time() - start_time
    elapsed_min = elapsed / 60
    
    print("\n" + "=" * 100)
    print(f"PORTFOLIO SCRAPING MONITOR - Iteration #{iteration} - Elapsed: {elapsed_min:.1f} minutes")
    print("=" * 100)
    
    # Overall stats
    print(f"\n[TOTAL COMPANIES] {stats['total']}")
    print(f"  YC Companies: {stats['yc_companies']}")
    print(f"  Antler Companies: {stats['antler_companies']}")
    
    # By source breakdown
    if stats['by_source']:
        print(f"\n[BY SOURCE]")
        for source, count in stats['by_source'].items():
            print(f"  {source}: {count}")
    
    # Ingestion rate
    print(f"\n[INGESTION RATE]")
    print(f"  Added in last minute: {stats['added_last_minute']}")
    print(f"  Added in last 5 minutes: {stats['added_last_5min']}")
    if elapsed_min > 0:
        rate = stats['total'] / elapsed_min
        print(f"  Average rate: {rate:.1f} companies/minute")
    
    # Data quality metrics
    comp = stats['completeness']
    print(f"\n[DATA QUALITY METRICS]")
    print(f"  Name: {comp['with_name']}/{comp['total']} ({comp['name_pct']:.1f}%)")
    print(f"  Domain: {comp['with_domain']}/{comp['total']} ({comp['domain_pct']:.1f}%)")
    print(f"  Stage: {comp['with_stage']}/{comp['total']} ({comp['stage_pct']:.1f}%)")
    print(f"  Focus Areas: {comp['with_focus_areas']}/{comp['total']} ({comp['focus_pct']:.1f}%)")
    print(f"  Employees: {comp['with_employees']}/{comp['total']} ({comp['employees_pct']:.1f}%)")
    print(f"  Funding: {comp['with_funding']}/{comp['total']} ({comp['funding_pct']:.1f}%)")
    
    # Overall quality score
    quality_score = (
        comp['name_pct'] + comp['domain_pct'] + comp['stage_pct'] + 
        comp['focus_pct'] + comp['employees_pct'] + comp['funding_pct']
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
    if stats['recent_companies']:
        print(f"\n[RECENTLY ADDED COMPANIES] (Last 10)")
        for i, company in enumerate(stats['recent_companies'][:10], 1):
            focus_str = company['focus_areas'][:50] if company['focus_areas'] else 'None'
            print(f"  {i}. {company['name']} ({company['domain']})")
            print(f"     Source: {company['source']}, Batch: {company['yc_batch'] or 'N/A'}, Stage: {company['stage'] or 'N/A'}")
            print(f"     Focus: {focus_str}")
    
    print("\n" + "=" * 100)

def main():
    """Main monitoring loop"""
    db_path = Path(__file__).parent / "celerio_scout.db"
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    print("=" * 100)
    print("PORTFOLIO SCRAPING CONTINUOUS MONITOR")
    print("=" * 100)
    print(f"Database: {db_path}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nMonitoring every 10 seconds...")
    print("Press Ctrl+C to stop")
    
    conn = duckdb.connect(str(db_path))
    start_time = time.time()
    iteration = 0
    last_total = 0
    
    try:
        while True:
            iteration += 1
            stats = get_database_stats(conn)
            
            # Show metrics
            print_metrics(stats, iteration, start_time)
            
            # Show change since last check
            if iteration > 1:
                new_companies = stats['total'] - last_total
                if new_companies > 0:
                    print(f"\n[PROGRESS] +{new_companies} new companies since last check!")
                else:
                    print(f"\n[PROGRESS] No new companies in last check")
            
            last_total = stats['total']
            
            # Wait before next check
            print(f"\nNext check in 10 seconds... (Ctrl+C to stop)")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 100)
        print("MONITORING STOPPED")
        print("=" * 100)
        final_stats = get_database_stats(conn)
        print_metrics(final_stats, iteration, start_time)
        print("\nFinal Summary:")
        print(f"  Total companies: {final_stats['total']}")
        print(f"  YC: {final_stats['yc_companies']}")
        print(f"  Antler: {final_stats['antler_companies']}")
        print(f"  Quality Score: {(final_stats['completeness']['name_pct'] + final_stats['completeness']['domain_pct'] + final_stats['completeness']['stage_pct'] + final_stats['completeness']['focus_pct'] + final_stats['completeness']['employees_pct'] + final_stats['completeness']['funding_pct']) / 6:.1f}%")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

