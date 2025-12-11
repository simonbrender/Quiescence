"""Verify the backend CSV file that the user is viewing"""
import csv
from pathlib import Path

csv_path = Path(__file__).parent / "companies_export.csv"

print("="*70)
print("VERIFYING BACKEND CSV FILE")
print("="*70)
print(f"File: {csv_path}")
print(f"Exists: {csv_path.exists()}")

if csv_path.exists():
    print(f"Size: {csv_path.stat().st_size:,} bytes")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"\nRows in CSV: {len(rows)}")
    
    if len(rows) > 0:
        print(f"\nFirst company:")
        print(f"  Name: {rows[0].get('name')}")
        print(f"  Focus Areas: {rows[0].get('focus_areas')}")
        print(f"  Has System.Object: {'System.Object' in rows[0].get('focus_areas', '')}")
        
        print(f"\nLast company:")
        print(f"  Name: {rows[-1].get('name')}")
        print(f"  Focus Areas: {rows[-1].get('focus_areas')}")
        
        # Check for System.Object
        system_object_count = sum(1 for r in rows if 'System.Object' in r.get('focus_areas', ''))
        print(f"\nCompanies with 'System.Object': {system_object_count}")
        
        if system_object_count == 0:
            print("[SUCCESS] No 'System.Object' found - all focus_areas are properly formatted!")
        else:
            print(f"[ERROR] Found {system_object_count} companies with 'System.Object'")
    else:
        print("[ERROR] CSV file is empty!")
else:
    print("[ERROR] CSV file does not exist!")

print("="*70)



