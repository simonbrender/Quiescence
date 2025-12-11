"""
Batch enrichment script to enrich all existing companies in the database
with stage, focus areas, employees, and funding data.
"""
import sys
import duckdb
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from data_enrichment import enrich_company_data
except ImportError:
    print("Warning: data_enrichment module not found, using basic enrichment")
    async def enrich_company_data(company, domain):
        return company

# Try to import web scraping tools for enrichment
try:
    import aiohttp
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False


async def infer_focus_area_from_domain(domain: str, name: str) -> List[str]:
    """Infer focus area from domain and company name"""
    focus_areas = []
    text = (domain + " " + name).lower()
    
    # AI/ML indicators
    if any(keyword in text for keyword in ['ai', 'ml', 'machine learning', 'artificial intelligence', 'deep learning', 'llm', 'gpt', 'neural']):
        focus_areas.append('AI/ML')
    
    # B2B SaaS indicators
    if any(keyword in text for keyword in ['saas', 'b2b', 'enterprise', 'platform', 'api', 'software']):
        focus_areas.append('B2B SaaS')
    
    # Fintech indicators
    if any(keyword in text for keyword in ['fintech', 'finance', 'payment', 'banking', 'crypto', 'blockchain']):
        focus_areas.append('Fintech')
    
    # DevTools indicators
    if any(keyword in text for keyword in ['dev', 'developer', 'tools', 'infrastructure', 'ci/cd', 'deployment']):
        focus_areas.append('DevTools')
    
    return focus_areas if focus_areas else ['B2B SaaS']  # Default to B2B SaaS


async def infer_stage_from_yc_batch(yc_batch: Optional[str]) -> Optional[str]:
    """Infer stage from YC batch"""
    if not yc_batch:
        return None
    
    # YC companies are typically Seed stage
    # Could be enhanced with actual raise data from Crunchbase
    return 'Seed'


async def enrich_company_batch(conn, companies: List[Dict], batch_size: int = 50):
    """Enrich a batch of companies"""
    enriched_count = 0
    updated_count = 0
    
    for i, company in enumerate(companies, 1):
        try:
            domain = company.get('domain', '').strip()
            name = company.get('name', '').strip()
            company_id = company.get('id')
            
            if not domain:
                continue
            
            print(f"[ENRICH] [{i}/{len(companies)}] Enriching {name} ({domain})...")
            
            # Check what data is missing
            needs_stage = not company.get('last_raise_stage')
            needs_focus = not company.get('focus_areas') or company.get('focus_areas') == '[]' or company.get('focus_areas') == ''
            needs_employees = not company.get('employee_count')
            needs_funding = not company.get('funding_amount')
            
            updates = {}
            
            # Infer focus areas from domain/name
            if needs_focus:
                focus_areas = await infer_focus_area_from_domain(domain, name)
                if focus_areas:
                    updates['focus_areas'] = json.dumps(focus_areas)
                    print(f"  → Focus areas: {focus_areas}")
            
            # Infer stage from YC batch
            if needs_stage:
                yc_batch = company.get('yc_batch')
                stage = await infer_stage_from_yc_batch(yc_batch)
                if stage:
                    updates['last_raise_stage'] = stage
                    print(f"  → Stage: {stage}")
                elif yc_batch:
                    # YC companies without explicit stage -> Seed
                    updates['last_raise_stage'] = 'Seed'
                    print(f"  → Stage: Seed (from YC batch)")
            
            # Try to use data_enrichment module if available
            try:
                enriched = await enrich_company_data(company, domain)
                if enriched and enriched != company:
                    # Merge enriched data
                    if enriched.get('last_raise_stage') and not updates.get('last_raise_stage'):
                        updates['last_raise_stage'] = enriched['last_raise_stage']
                    if enriched.get('focus_areas') and not updates.get('focus_areas'):
                        if isinstance(enriched['focus_areas'], list):
                            updates['focus_areas'] = json.dumps(enriched['focus_areas'])
                        else:
                            updates['focus_areas'] = enriched['focus_areas']
                    if enriched.get('employee_count') and not updates.get('employee_count'):
                        updates['employee_count'] = enriched['employee_count']
                    if enriched.get('funding_amount') and not updates.get('funding_amount'):
                        updates['funding_amount'] = enriched['funding_amount']
            except Exception as e:
                print(f"  → Enrichment module error (continuing): {e}")
            
            # Update database if we have updates
            if updates:
                set_clauses = []
                params = []
                for key, value in updates.items():
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
                
                set_clauses.append("updated_at = ?")
                params.append(datetime.now())
                params.append(company_id)
                
                update_query = f"""
                    UPDATE companies 
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                
                conn.execute(update_query, params)
                conn.commit()
                updated_count += 1
                print(f"  ✓ Updated {len(updates)} fields")
            else:
                print(f"  ⊗ No updates needed")
            
            enriched_count += 1
            
            # Small delay to avoid overwhelming the system
            if i % 10 == 0:
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"  ✗ Error enriching company {company.get('name', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return enriched_count, updated_count


async def main():
    """Main enrichment function"""
    print("=" * 80)
    print("BATCH COMPANY ENRICHMENT")
    print("=" * 80)
    
    # Connect to database
    db_path = Path(__file__).parent / "celerio_scout.db"
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    conn = duckdb.connect(str(db_path))
    
    try:
        # Get all companies that need enrichment
        print("\n[STEP 1] Fetching companies from database...")
        companies = conn.execute("""
            SELECT id, name, domain, source, yc_batch, last_raise_stage, 
                   focus_areas, employee_count, funding_amount
            FROM companies
            ORDER BY created_at DESC
        """).fetchall()
        
        columns = ['id', 'name', 'domain', 'source', 'yc_batch', 'last_raise_stage',
                  'focus_areas', 'employee_count', 'funding_amount']
        company_dicts = [dict(zip(columns, row)) for row in companies]
        
        total = len(company_dicts)
        print(f"Found {total} companies")
        
        # Count how many need enrichment
        need_stage = sum(1 for c in company_dicts if not c.get('last_raise_stage'))
        need_focus = sum(1 for c in company_dicts if not c.get('focus_areas') or c.get('focus_areas') == '[]' or c.get('focus_areas') == '')
        need_employees = sum(1 for c in company_dicts if not c.get('employee_count'))
        need_funding = sum(1 for c in company_dicts if not c.get('funding_amount'))
        
        print(f"\nEnrichment needs:")
        print(f"  Stage: {need_stage}/{total} ({need_stage/total*100:.1f}%)")
        print(f"  Focus areas: {need_focus}/{total} ({need_focus/total*100:.1f}%)")
        print(f"  Employees: {need_employees}/{total} ({need_employees/total*100:.1f}%)")
        print(f"  Funding: {need_funding}/{total} ({need_funding/total*100:.1f}%)")
        
        if total == 0:
            print("No companies to enrich")
            return
        
        # Enrich companies in batches
        print(f"\n[STEP 2] Enriching companies...")
        enriched, updated = await enrich_company_batch(conn, company_dicts)
        
        print(f"\n[STEP 3] Summary:")
        print(f"  Processed: {enriched}/{total}")
        print(f"  Updated: {updated}/{total}")
        
        # Verify enrichment
        print(f"\n[STEP 4] Verifying enrichment...")
        after_companies = conn.execute("""
            SELECT COUNT(*) as total,
                   COUNT(last_raise_stage) as with_stage,
                   COUNT(focus_areas) as with_focus,
                   COUNT(employee_count) as with_employees,
                   COUNT(funding_amount) as with_funding
            FROM companies
            WHERE focus_areas IS NOT NULL AND focus_areas != '' AND focus_areas != '[]'
        """).fetchone()
        
        total_after, stage_after, focus_after, emp_after, fund_after = after_companies
        
        print(f"  Total companies: {total_after}")
        print(f"  With stage: {stage_after} ({stage_after/total_after*100:.1f}%)")
        print(f"  With focus areas: {focus_after} ({focus_after/total_after*100:.1f}%)")
        print(f"  With employees: {emp_after} ({emp_after/total_after*100:.1f}%)")
        print(f"  With funding: {fund_after} ({fund_after/total_after*100:.1f}%)")
        
        print("\n" + "=" * 80)
        print("ENRICHMENT COMPLETE!")
        print("=" * 80)
        
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())

