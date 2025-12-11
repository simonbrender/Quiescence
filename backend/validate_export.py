"""Validate the CSV export to ensure all companies are exported correctly"""
import csv
import json
import requests
from pathlib import Path

def validate_csv_export():
    """Validate the exported CSV file"""
    csv_path = Path(__file__).parent.parent / "companies_export.csv"
    
    if not csv_path.exists():
        print(f"[ERROR] CSV file not found: {csv_path}")
        return False
    
    # Get expected count from API
    try:
        stats = requests.get('http://localhost:8000/stats', timeout=5).json()
        expected_count = stats.get('total_companies', 0)
        print(f"Expected companies in database: {expected_count}")
    except Exception as e:
        print(f"[WARN] Could not get stats from API: {e}")
        expected_count = None
    
    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"\nCSV File: {csv_path}")
    print(f"Rows in CSV: {len(rows)}")
    if expected_count:
        if len(rows) == expected_count:
            print(f"[OK] All {expected_count} companies exported!")
        else:
            print(f"[WARN] Missing {expected_count - len(rows)} companies")
    
    # Validate focus_areas format
    valid_format = 0
    invalid_format = 0
    empty_format = 0
    system_object_found = False
    
    for i, row in enumerate(rows):
        focus_areas = row.get('focus_areas', '')
        
        if not focus_areas or focus_areas.strip() == '':
            empty_format += 1
        elif 'System.Object' in focus_areas:
            system_object_found = True
            invalid_format += 1
            if invalid_format == 1:  # Show first error
                print(f"\n[ERROR] Found 'System.Object' in row {i+1}: {focus_areas[:100]}")
        elif focus_areas.startswith('[') and focus_areas.endswith(']'):
            # Try to parse as JSON
            try:
                parsed = json.loads(focus_areas)
                if isinstance(parsed, list):
                    valid_format += 1
                else:
                    invalid_format += 1
            except:
                invalid_format += 1
        else:
            invalid_format += 1
    
    print(f"\nFocus Areas Validation:")
    print(f"  [OK] Valid JSON arrays: {valid_format}")
    print(f"  [WARN] Invalid format: {invalid_format}")
    print(f"  [EMPTY] Empty/null: {empty_format}")
    
    if system_object_found:
        print(f"\n[ERROR] CSV export failed - 'System.Object' found in focus_areas!")
        return False
    
    if invalid_format == 0:
        print(f"  [OK] All focus_areas are properly formatted!")
        return True
    else:
        print(f"  [WARN] {invalid_format} companies have invalid focus_areas format")
        return False

if __name__ == "__main__":
    print("="*60)
    print("CSV EXPORT VALIDATION")
    print("="*60)
    success = validate_csv_export()
    print("\n" + "="*60)
    if success:
        print("[SUCCESS] CSV export validation passed!")
    else:
        print("[FAILED] CSV export validation failed!")
    print("="*60)



