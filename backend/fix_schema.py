"""Fix database schema by adding missing columns"""
import duckdb

conn = duckdb.connect("celerio_scout.db")

# Required columns
required_columns = [
    ('last_raise_stage', 'TEXT'),
    ('last_raise_date', 'DATE'),
    ('fund_tier', 'TEXT'),
    ('focus_areas', 'TEXT'),
    ('funding_amount', 'REAL'),
    ('funding_currency', 'TEXT'),
    ('employee_count', 'INTEGER')
]

def column_exists(table_name, column_name):
    """Check if a column exists"""
    try:
        result = conn.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = ? AND column_name = ?
        """, (table_name, column_name)).fetchone()
        return result is not None
    except:
        return False

print("Checking and adding missing columns...")
for col_name, col_type in required_columns:
    exists = column_exists('companies', col_name)
    print(f"Column '{col_name}': {'EXISTS' if exists else 'MISSING'}")
    if not exists:
        try:
            conn.execute(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}")
            conn.commit()
            print(f"  [OK] Added column '{col_name}'")
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"  [ERROR] Error adding column '{col_name}': {e}")
            else:
                print(f"  [OK] Column '{col_name}' already exists")

print("\nVerifying columns...")
cols = conn.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'companies' 
    ORDER BY column_name
""").fetchall()
print(f"Total columns: {len(cols)}")
for col in cols:
    print(f"  - {col[0]}")

conn.close()
print("\nSchema fix complete!")

