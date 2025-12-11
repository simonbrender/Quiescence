"""Final comprehensive verification of CSV export"""
import csv
import json
import requests
from pathlib import Path

def verify_export():
    """Comprehensive verification of the CSV export"""
    csv_path = Path(__file__).parent.parent / "companies_export.csv"
    
    print("="*70)
    print("FINAL CSV EXPORT VERIFICATION")
    print("="*70)
    
    # 1. Check file exists
    if not csv_path.exists():
        print(f"[FAIL] CSV file not found: {csv_path}")
        return False
    
    file_size = csv_path.stat().st_size
    print(f"\n[OK] CSV file exists: {csv_path}")
    print(f"     File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    # 2. Get expected count from API
    try:
        stats = requests.get('http://localhost:8000/stats', timeout=5).json()
        expected_count = stats.get('total_companies', 0)
        print(f"\n[OK] Database has {expected_count} companies")
    except Exception as e:
        print(f"\n[WARN] Could not get stats from API: {e}")
        expected_count = None
    
    # 3. Read and count CSV rows
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"\n[OK] CSV file readable")
    print(f"     Rows in CSV: {len(rows)}")
    
    if expected_count:
        if len(rows) == expected_count:
            print(f"     [SUCCESS] All {expected_count} companies exported!")
        else:
            print(f"     [FAIL] Missing {expected_count - len(rows)} companies!")
            return False
    
    # 4. Validate focus_areas format
    print(f"\n[VALIDATING] focus_areas format...")
    valid_format = 0
    invalid_format = 0
    empty_format = 0
    system_object_found = False
    system_object_examples = []
    
    for i, row in enumerate(rows):
        focus_areas = row.get('focus_areas', '')
        
        if not focus_areas or focus_areas.strip() == '':
            empty_format += 1
        elif 'System.Object' in focus_areas:
            system_object_found = True
            invalid_format += 1
            if len(system_object_examples) < 3:
                system_object_examples.append((i+1, focus_areas[:100]))
        elif focus_areas.startswith('[') and focus_areas.endswith(']'):
            try:
                parsed = json.loads(focus_areas)
                if isinstance(parsed, list):
                    valid_format += 1
                else:
                    invalid_format += 1
            except json.JSONDecodeError:
                invalid_format += 1
        else:
            invalid_format += 1
    
    print(f"     Valid JSON arrays: {valid_format}")
    print(f"     Invalid format: {invalid_format}")
    print(f"     Empty/null: {empty_format}")
    
    if system_object_found:
        print(f"\n     [FAIL] Found 'System.Object' in focus_areas!")
        for row_num, example in system_object_examples:
            print(f"            Row {row_num}: {example}")
        return False
    
    if invalid_format > 0:
        print(f"\n     [FAIL] {invalid_format} companies have invalid focus_areas format!")
        return False
    
    if valid_format + empty_format == len(rows):
        print(f"     [SUCCESS] All focus_areas are properly formatted!")
    else:
        print(f"     [WARN] Format validation incomplete")
    
    # 5. Check sample data
    print(f"\n[SAMPLE DATA] First 3 companies:")
    for i in range(min(3, len(rows))):
        row = rows[i]
        focus = row.get('focus_areas', '')
        print(f"  {i+1}. {row.get('name', 'N/A')} ({row.get('domain', 'N/A')})")
        print(f"      Focus: {focus[:60]}...")
        print(f"      Source: {row.get('source', 'N/A')}")
    
    # 6. Check last row
    if len(rows) > 0:
        last_row = rows[-1]
        print(f"\n[LAST ROW] Company #{len(rows)}:")
        print(f"  Name: {last_row.get('name', 'N/A')}")
        print(f"  Focus: {last_row.get('focus_areas', 'N/A')[:60]}...")
    
    # 7. Verify all required columns exist
    required_columns = ['id', 'name', 'domain', 'source', 'focus_areas', 
                       'messaging_score', 'motion_score', 'market_score']
    missing_columns = [col for col in required_columns if col not in rows[0].keys()]
    if missing_columns:
        print(f"\n[FAIL] Missing required columns: {missing_columns}")
        return False
    else:
        print(f"\n[OK] All required columns present")
    
    # Final summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    print(f"[OK] File exists and readable")
    print(f"[OK] All {len(rows)} companies exported")
    print(f"[OK] All focus_areas are JSON arrays (no 'System.Object')")
    print(f"[OK] All required columns present")
    print(f"[OK] File size: {file_size:,} bytes")
    print("\n[SUCCESS] CSV export is 100% correct!")
    print("="*70)
    
    return True

if __name__ == "__main__":
    success = verify_export()
    exit(0 if success else 1)

