"""
Script to scrape real portfolio companies and populate database
This will scrape YC batches and other VC portfolios, then enrich with OSINT data
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import conn
from osint_sources import scrape_yc_batch
from portfolio_scraper import PortfolioScraper
from triangulate_companies import triangulate_companies
from data_enrichment import enrich_company_data
from scorer import calculate_scores
from datetime import datetime
import json

async def scrape_and_populate():
    """Scrape real portfolio companies and populate database"""
    print("=" * 60)
    print("CELERIO SCOUT - Portfolio Scraping & Population")
    print("=" * 60)
    
    scraper = PortfolioScraper()
    
    # Get available portfolios from database
    portfolios = scraper.get_available_portfolios(db_conn=conn)
    print(f"\nFound {len(portfolios)} portfolios to scrape")
    
    all_companies = []
    
    # Triangulate companies from multiple sources
    print("\n[1/3] Triangulating companies from multiple sources...")
    try:
        triangulated = await triangulate_companies()
        print(f"  Found {len(triangulated)} companies from triangulation")
        all_companies.extend(triangulated)
    except Exception as e:
        print(f"  Error in triangulation: {e}")
    
    # Also try direct YC batch scraping
    print("\n[1b/3] Scraping Y Combinator batches directly...")
    yc_batches = ['W22', 'S22', 'W23', 'S23']
    for batch in yc_batches:
        print(f"  Scraping YC batch {batch}...")
        try:
            companies = await scrape_yc_batch(batch)
            print(f"    Found {len(companies)} companies")
            all_companies.extend(companies)
            await asyncio.sleep(1)  # Rate limiting
        except Exception as e:
            print(f"    Error scraping {batch}: {e}")
    
    # Scrape other VC portfolios if available
    print("\n[2/3] Scraping VC portfolios...")
    for portfolio in portfolios[:3]:  # Limit to first 3 for now
        firm_name = portfolio.get('firm_name', '')
        portfolio_url = portfolio.get('portfolio_url') or portfolio.get('url', '')
        
        if not portfolio_url or firm_name == 'Y Combinator':
            continue
        
        print(f"  Scraping {firm_name}...")
        try:
            companies = await scraper.scrape_portfolio(
                firm_name,
                portfolio_url,
                portfolio.get('type', 'VC')
            )
            print(f"    Found {len(companies)} companies")
            all_companies.extend(companies)
            await asyncio.sleep(2)  # Rate limiting
        except Exception as e:
            print(f"    Error scraping {firm_name}: {e}")
    
    print(f"\nTotal companies scraped: {len(all_companies)}")
    
    # Deduplicate by domain
    seen_domains = set()
    unique_companies = []
    for company in all_companies:
        domain = company.get('domain', '').lower()
        if domain and domain not in seen_domains:
            seen_domains.add(domain)
            unique_companies.append(company)
    
    print(f"Unique companies (by domain): {len(unique_companies)}")
    
    # Enrich and store companies
    print("\n[3/3] Enriching and storing companies...")
    added_count = 0
    updated_count = 0
    error_count = 0
    
    for i, company in enumerate(unique_companies, 1):
        try:
            domain = company.get('domain', '')
            company_name = company.get('name', '')
            
            if not domain or not company_name:
                continue
            
            print(f"  [{i}/{len(unique_companies)}] Processing {company_name} ({domain})...")
            
            # Enrich company data
            enriched = await enrich_company_data(company, domain)
            
            # Calculate scores (this may take time)
            print(f"    Calculating 3M scores...")
            scores = await calculate_scores(domain, company_name)
            
            # Create company record
            company_id = hash(domain) % 1000000
            now = datetime.now()
            
            # Parse focus areas
            focus_areas = enriched.get('focus_areas', [])
            if isinstance(focus_areas, str):
                try:
                    focus_areas = json.loads(focus_areas)
                except:
                    focus_areas = [focus_areas] if focus_areas else []
            
            # Determine fund tier
            fund_tier = enriched.get('fund_tier')
            if not fund_tier and company.get('source') == 'yc':
                fund_tier = "Tier 1"
            
            # Estimate raise date from YC batch
            last_raise_date = enriched.get('last_raise_date')
            last_raise_stage = enriched.get('last_raise_stage')
            yc_batch = company.get('yc_batch', '')
            if yc_batch and not last_raise_date:
                if yc_batch.startswith('W'):
                    year = 2000 + int(yc_batch[1:])
                    last_raise_date = datetime(year, 2, 1).date()
                    last_raise_stage = "Seed"
                elif yc_batch.startswith('S'):
                    year = 2000 + int(yc_batch[1:])
                    last_raise_date = datetime(year, 8, 1).date()
                    last_raise_stage = "Seed"
            
            company_record = {
                'id': company_id,
                'name': company_name,
                'domain': domain,
                'yc_batch': yc_batch,
                'source': company.get('source', 'portfolio'),
                'messaging_score': scores['messaging_score'],
                'motion_score': scores['motion_score'],
                'market_score': scores['market_score'],
                'stall_probability': scores['stall_probability'],
                'signals': json.dumps(scores['signals']),
                'funding_amount': enriched.get('funding_amount'),
                'funding_currency': enriched.get('funding_currency', 'USD'),
                'employee_count': enriched.get('employee_count'),
                'last_raise_date': last_raise_date,
                'last_raise_stage': last_raise_stage,
                'fund_tier': fund_tier,
                'focus_areas': json.dumps(focus_areas),
                'created_at': now,
                'updated_at': now
            }
            
            # Check if exists
            existing = conn.execute(
                "SELECT id FROM companies WHERE id = ? OR domain = ?",
                (company_id, domain)
            ).fetchone()
            
            if existing:
                conn.execute("""
                    UPDATE companies SET
                        name = ?, domain = ?, yc_batch = ?, source = ?,
                        messaging_score = ?, motion_score = ?, market_score = ?,
                        stall_probability = ?, signals = ?, 
                        funding_amount = ?, funding_currency = ?, employee_count = ?,
                        last_raise_date = ?, last_raise_stage = ?, fund_tier = ?,
                        focus_areas = ?, updated_at = ?
                    WHERE id = ? OR domain = ?
                """, (
                    company_record['name'],
                    company_record['domain'],
                    company_record['yc_batch'],
                    company_record['source'],
                    company_record['messaging_score'],
                    company_record['motion_score'],
                    company_record['market_score'],
                    company_record['stall_probability'],
                    company_record['signals'],
                    company_record['funding_amount'],
                    company_record['funding_currency'],
                    company_record['employee_count'],
                    company_record['last_raise_date'],
                    company_record['last_raise_stage'],
                    company_record['fund_tier'],
                    company_record['focus_areas'],
                    company_record['updated_at'],
                    company_id,
                    domain
                ))
                updated_count += 1
            else:
                conn.execute("""
                    INSERT INTO companies 
                    (id, name, domain, yc_batch, source, messaging_score, motion_score, market_score, 
                     stall_probability, signals, funding_amount, funding_currency, employee_count,
                     last_raise_date, last_raise_stage, fund_tier, focus_areas, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    company_record['id'],
                    company_record['name'],
                    company_record['domain'],
                    company_record['yc_batch'],
                    company_record['source'],
                    company_record['messaging_score'],
                    company_record['motion_score'],
                    company_record['market_score'],
                    company_record['stall_probability'],
                    company_record['signals'],
                    company_record['funding_amount'],
                    company_record['funding_currency'],
                    company_record['employee_count'],
                    company_record['last_raise_date'],
                    company_record['last_raise_stage'],
                    company_record['fund_tier'],
                    company_record['focus_areas'],
                    company_record['created_at'],
                    company_record['updated_at']
                ))
                added_count += 1
            
            # Rate limiting between companies
            await asyncio.sleep(0.5)
            
        except Exception as e:
            error_count += 1
            print(f"    ✗ Error: {e}")
            continue
    
    conn.commit()
    
    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    print(f"Added: {added_count} companies")
    print(f"Updated: {updated_count} companies")
    print(f"Errors: {error_count} companies")
    total = conn.execute('SELECT COUNT(*) FROM companies').fetchone()[0]
    print(f"Total companies in database: {total}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(scrape_and_populate())

