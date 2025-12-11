"""Force export all companies directly from API"""
import requests
import csv
import json
from pathlib import Path

def force_export():
    """Force export all companies to CSV"""
    print("="*70)
    print("FORCING EXPORT OF ALL COMPANIES")
    print("="*70)
    
    # Get all companies from export endpoint
    print("\n[1] Fetching all companies from API...")
    try:
        response = requests.get('http://localhost:8000/companies/export', timeout=120)
        if response.status_code != 200:
            print(f"[ERROR] API returned status {response.status_code}")
            return False
        
        companies = response.json()
        print(f"[OK] Retrieved {len(companies)} companies from API")
    except Exception as e:
        print(f"[ERROR] Failed to fetch companies: {e}")
        return False
    
    if not companies:
        print("[ERROR] No companies returned")
        return False
    
    # Write to CSV
    print(f"\n[2] Writing {len(companies)} companies to CSV...")
    output_path = Path(__file__).parent.parent / "companies_export.csv"
    
    fieldnames = list(companies[0].keys())
    print(f"[OK] Found {len(fieldnames)} columns")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        
        written = 0
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
            written += 1
            if written % 100 == 0:
                print(f"  Written {written}/{len(companies)} companies...")
    
    print(f"[OK] Written {written} companies to {output_path}")
    
    # Verify
    print(f"\n[3] Verifying CSV file...")
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        csv_rows = list(reader)
    
    print(f"[OK] CSV file has {len(csv_rows)} rows")
    
    if len(csv_rows) == len(companies):
        print(f"[SUCCESS] All {len(companies)} companies exported correctly!")
    else:
        print(f"[ERROR] Mismatch: CSV has {len(csv_rows)}, expected {len(companies)}")
        return False
    
    # Check focus_areas format
    print(f"\n[4] Checking focus_areas format...")
    valid = 0
    invalid = 0
    for row in csv_rows[:100]:  # Check first 100
        focus = row.get('focus_areas', '')
        if focus.startswith('[') and focus.endswith(']'):
            valid += 1
        elif 'System.Object' in focus:
            invalid += 1
            print(f"  [ERROR] Found System.Object in row: {row.get('name', 'unknown')}")
    
    print(f"[OK] Sample check: {valid} valid, {invalid} invalid")
    
    print("\n" + "="*70)
    print(f"[SUCCESS] Export complete: {len(companies)} companies")
    print(f"File: {output_path}")
    print(f"Size: {output_path.stat().st_size:,} bytes")
    print("="*70)
    
    return True

if __name__ == "__main__":
    success = force_export()
    exit(0 if success else 1)



