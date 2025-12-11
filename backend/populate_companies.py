"""
Script to populate database with real companies from YC batches
This will scrape YC companies and enrich them with funding/employee data
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import conn
from seeds import scrape_yc_companies
from data_enrichment import enrich_company_data
from scorer import calculate_scores
from datetime import datetime
import json

async def populate_yc_companies():
    """Populate database with YC companies from recent batches"""
    print("Scraping YC companies from batches W22, S22, W23, S23...")
    
    # Scrape YC companies
    companies = await scrape_yc_companies(['W22', 'S22', 'W23', 'S23'])
    print(f"Found {len(companies)} YC companies")
    
    added_count = 0
    updated_count = 0
    
    for company in companies:
        try:
            domain = company.get('domain', '')
            if not domain:
                # Try to extract domain from name
                domain = company['name'].lower().replace(' ', '').replace('-', '') + '.com'
            
            # Enrich company data
            enriched = await enrich_company_data(company, domain)
            
            # Calculate scores
            scores = await calculate_scores(domain, company['name'])
            
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
            
            # Determine fund tier (YC is Tier 1)
            fund_tier = "Tier 1"
            
            # Estimate raise date from YC batch
            last_raise_date = None
            last_raise_stage = "Seed"
            yc_batch = company.get('yc_batch', '')
            if yc_batch:
                if yc_batch.startswith('W'):
                    year = 2000 + int(yc_batch[1:])
                    last_raise_date = datetime(year, 2, 1).date()
                elif yc_batch.startswith('S'):
                    year = 2000 + int(yc_batch[1:])
                    last_raise_date = datetime(year, 8, 1).date()
            
            company_record = {
                'id': company_id,
                'name': company['name'],
                'domain': domain,
                'yc_batch': yc_batch,
                'source': 'yc',
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
            
            # Rate limiting
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"Error processing company {company.get('name', 'unknown')}: {e}")
            continue
    
    conn.commit()
    print(f"\nCompleted! Added {added_count} new companies, updated {updated_count} existing companies")
    print(f"Total companies in database: {conn.execute('SELECT COUNT(*) FROM companies').fetchone()[0]}")

if __name__ == "__main__":
    asyncio.run(populate_yc_companies())





