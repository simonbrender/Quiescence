"""Test database queries directly to understand why searches return 0 results"""
import sys
import duckdb
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

conn = duckdb.connect('celerio_scout.db', read_only=True)

print("=" * 80)
print("DATABASE ANALYSIS")
print("=" * 80)

# Total companies
total = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
print(f"\nTotal companies: {total}")

# Check stages
stages = conn.execute("SELECT DISTINCT last_raise_stage FROM companies WHERE last_raise_stage IS NOT NULL LIMIT 20").fetchall()
print(f"\nUnique stages found: {[s[0] for s in stages]}")

# Check focus areas
focus_sample = conn.execute("SELECT focus_areas FROM companies WHERE focus_areas IS NOT NULL LIMIT 5").fetchall()
print(f"\nSample focus_areas:")
for f in focus_sample:
    print(f"  {f[0]}")

# Test a simple query
print("\n" + "=" * 80)
print("TESTING QUERIES")
print("=" * 80)

# Query 1: Series A companies
query1 = "SELECT COUNT(*) FROM companies WHERE last_raise_stage = 'Series A'"
result1 = conn.execute(query1).fetchone()[0]
print(f"\nSeries A companies: {result1}")

# Query 2: AI/ML companies
query2 = "SELECT COUNT(*) FROM companies WHERE focus_areas LIKE '%AI/ML%'"
result2 = conn.execute(query2).fetchone()[0]
print(f"AI/ML companies: {result2}")

# Query 3: Series A AND AI/ML
query3 = "SELECT COUNT(*) FROM companies WHERE last_raise_stage = 'Series A' AND focus_areas LIKE '%AI/ML%'"
result3 = conn.execute(query3).fetchone()[0]
print(f"Series A AND AI/ML: {result3}")

# Query 4: Check what focus_areas actually contain
print("\nSample companies with focus_areas:")
sample = conn.execute("SELECT name, domain, focus_areas FROM companies WHERE focus_areas IS NOT NULL LIMIT 10").fetchall()
for row in sample:
    print(f"  {row[0]} ({row[1]}): {row[2]}")

# Query 5: Check stages distribution
print("\nStage distribution:")
stage_dist = conn.execute("SELECT last_raise_stage, COUNT(*) as cnt FROM companies WHERE last_raise_stage IS NOT NULL GROUP BY last_raise_stage ORDER BY cnt DESC").fetchall()
for stage, count in stage_dist:
    print(f"  {stage}: {count}")

conn.close()




