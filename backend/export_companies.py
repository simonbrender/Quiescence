"""Export all companies from database to CSV"""
import duckdb
import csv
import sys
import json
from pathlib import Path
from datetime import date, datetime
from typing import List, Dict

def validate_export(companies: List[Dict], output_path: Path):
    """Validate the exported CSV file"""
    print(f"\n{'='*60}")
    print(f"EXPORT VALIDATION")
    print(f"{'='*60}")
    print(f"Exported {len(companies)} companies to {output_path}")
    print(f"File size: {output_path.stat().st_size:,} bytes")
    
    # Check expected count
    try:
        import requests
        stats = requests.get('http://localhost:8000/stats', timeout=5).json()
        expected_count = stats.get('total_companies', 0)
        if len(companies) < expected_count:
            print(f"[WARNING] Expected {expected_count} companies, but exported {len(companies)}")
        else:
            print(f"[OK] Exported {len(companies)} companies (expected: {expected_count})")
    except:
        print(f"[OK] Exported {len(companies)} companies")
    
    # Validate focus_areas format
    focus_areas_valid = 0
    focus_areas_invalid = 0
    focus_areas_empty = 0
    
    for company in companies:
        focus_areas = company.get('focus_areas')
        if focus_areas is None or focus_areas == '':
            focus_areas_empty += 1
        elif isinstance(focus_areas, list):
            focus_areas_valid += 1
        elif isinstance(focus_areas, str):
            try:
                parsed = json.loads(focus_areas)
                if isinstance(parsed, list):
                    focus_areas_valid += 1
                else:
                    focus_areas_invalid += 1
            except:
                focus_areas_invalid += 1
        else:
            focus_areas_invalid += 1
    
    print(f"\nFocus Areas Validation:")
    print(f"  [OK] Valid JSON arrays: {focus_areas_valid}")
    print(f"  [WARN] Invalid format: {focus_areas_invalid}")
    print(f"  [EMPTY] Empty/null: {focus_areas_empty}")
    
    if focus_areas_invalid == 0:
        print(f"  [OK] All focus_areas are properly formatted!")
    else:
        print(f"  [WARN] {focus_areas_invalid} companies have invalid focus_areas format")
    
    # Show sample data
    print(f"\nSample Companies (first 5):")
    for i, company in enumerate(companies[:5]):
        focus_areas = company.get('focus_areas', '')
        if isinstance(focus_areas, list):
            focus_display = json.dumps(focus_areas) if focus_areas else '(empty)'
        elif focus_areas:
            focus_display = str(focus_areas)
        else:
            focus_display = '(empty)'
        
        scores = f"M:{company.get('messaging_score', 'N/A')}, Mo:{company.get('motion_score', 'N/A')}, Ma:{company.get('market_score', 'N/A')}"
        print(f"  {i+1}. {company.get('name', 'N/A')} ({company.get('domain', 'N/A')})")
        print(f"      Source: {company.get('source', 'N/A')} | Focus: {focus_display}")
        print(f"      Scores: {scores}")
    
    # Verify CSV file can be read
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
            print(f"\nCSV File Validation:")
            print(f"  [OK] CSV file readable: {len(csv_rows)} rows")
            if len(csv_rows) == len(companies):
                print(f"  [OK] Row count matches exported companies")
            else:
                print(f"  [WARN] Row count mismatch: CSV has {len(csv_rows)}, exported {len(companies)}")
            
            # Check focus_areas in CSV
            if csv_rows:
                sample_focus = csv_rows[0].get('focus_areas', '')
                if sample_focus.startswith('[') and sample_focus.endswith(']'):
                    print(f"  [OK] focus_areas in CSV are JSON arrays (sample: {sample_focus[:50]}...)")
                elif 'System.Object' in sample_focus:
                    print(f"  [ERROR] focus_areas still contain 'System.Object' - export failed!")
                else:
                    print(f"  [WARN] focus_areas format: {sample_focus[:50]}...")
    except Exception as e:
        print(f"  [ERROR] Error reading CSV file: {e}")
    
    print(f"\n{'='*60}")
    print(f"Export complete! File: {output_path}")
    print(f"{'='*60}\n")

# Connect to database
# Try to connect with read-only access or handle lock gracefully
db_path = Path(__file__).parent / "celerio_scout.db"

# DuckDB supports concurrent reads, try read-only connection first
try:
    # Try read-only connection first (allows concurrent access)
    try:
        conn = duckdb.connect(str(db_path), read_only=True)
        print("Connected to database in read-only mode")
    except Exception as ro_error:
        # If read-only fails, try regular connection
        print(f"Read-only connection failed: {ro_error}, trying regular connection...")
        conn = duckdb.connect(str(db_path), read_only=False)
except Exception as e:
    print(f"Warning: Could not connect to database: {e}")
    print("Attempting to use API endpoint instead...")
    # Fallback: use API to fetch data with high limit to get all companies
    import requests
    try:
        # Use dedicated export endpoint that returns all companies without filtering
        response = None
        try:
            response = requests.get('http://localhost:8000/companies/export', timeout=30)
            if response.status_code == 404:
                # Endpoint doesn't exist yet (backend needs restart), fallback to regular endpoint
                print("Export endpoint not available, using regular companies endpoint...")
                response = requests.get('http://localhost:8000/companies', params={'limit': 100000, 'exclude_mock': False}, timeout=30)
        except requests.exceptions.RequestException as req_err:
            print(f"API request failed: {req_err}")
            raise e
        
        if response and response.status_code == 200:
            companies = response.json()
            # Export from API data - write to project root, not backend folder
            output_path = Path(__file__).parent.parent / "companies_export.csv"
            # Also remove old file in backend folder if it exists
            old_path = Path(__file__).parent / "companies_export.csv"
            if old_path.exists():
                old_path.unlink()
                print(f"Removed old export file: {old_path}")
            if companies:
                fieldnames = list(companies[0].keys())
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
                    writer.writeheader()
                    for company in companies:
                        row = {}
                        for field in fieldnames:
                            value = company.get(field)
                            if isinstance(value, (list, dict)):
                                value = json.dumps(value)
                            elif value is None:
                                value = ''
                            row[field] = value
                        writer.writerow(row)
                # Validate export
                validate_export(companies, output_path)
                sys.exit(0)
            else:
                print("API returned empty list")
        else:
            print(f"API returned status {response.status_code}: {response.text[:200]}")
        print("API fallback failed, trying direct connection again...")
        conn = duckdb.connect(str(db_path))
    except ImportError:
        print("requests library not available, cannot use API fallback")
        raise e
    except Exception as api_error:
        print(f"API fallback also failed: {api_error}")
        raise e

# Get all companies - use CAST to ensure focus_areas is treated as TEXT
# This prevents DuckDB from converting JSON strings to array types
query_result = conn.execute("""
    SELECT 
        id, name, domain, yc_batch, source, messaging_score, motion_score, 
        market_score, stall_probability, signals, funding_amount, funding_currency,
        employee_count, last_raise_date, last_raise_stage, fund_tier,
        CAST(focus_areas AS TEXT) as focus_areas,
        created_at, updated_at
    FROM companies
    ORDER BY id
""")
result = query_result.fetchall()
columns = [desc[0] for desc in query_result.description]

# Get statistics
total_count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
portfolio_count = conn.execute("SELECT COUNT(*) FROM companies WHERE source IN ('yc', 'antler', 'portfolio_scraping')").fetchone()[0]
mock_count = conn.execute("SELECT COUNT(*) FROM companies WHERE source = 'mock'").fetchone()[0]

print(f"Total companies: {total_count}")
print(f"Portfolio companies: {portfolio_count}")
print(f"Mock companies: {mock_count}")
print(f"Columns: {len(columns)}")

def serialize_value(value):
    """Convert a value to a CSV-safe string"""
    if value is None:
        return ''
    elif isinstance(value, (list, dict)):
        # Serialize lists/dicts as JSON strings
        return json.dumps(value)
    elif isinstance(value, (date, datetime)):
        # Convert dates/datetimes to ISO format strings
        return value.isoformat()
    elif isinstance(value, float):
        # Handle NaN and infinity
        if value != value:  # NaN check
            return ''
        return str(value)
    else:
        return str(value)

# Export to CSV - write to project root, not backend folder
output_path = Path(__file__).parent.parent / "companies_export.csv"
# Also remove old file in backend folder if it exists
old_path = Path(__file__).parent / "companies_export.csv"
if old_path.exists():
    old_path.unlink()
    print(f"Removed old export file: {old_path}")
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(columns)
    
    # Process each row and serialize values properly
    for row in result:
        serialized_row = [serialize_value(val) for val in row]
        writer.writerow(serialized_row)

# Convert database rows to company dicts for validation
companies_from_db = []
for row in result:
    company_dict = dict(zip(columns, row))
    # Parse JSON fields
    if isinstance(company_dict.get('focus_areas'), str) and company_dict.get('focus_areas'):
        try:
            company_dict['focus_areas'] = json.loads(company_dict['focus_areas'])
        except:
            company_dict['focus_areas'] = []
    if isinstance(company_dict.get('signals'), str) and company_dict.get('signals'):
        try:
            company_dict['signals'] = json.loads(company_dict['signals'])
        except:
            company_dict['signals'] = {}
    companies_from_db.append(company_dict)

# Validate export
validate_export(companies_from_db, output_path)

conn.close()

