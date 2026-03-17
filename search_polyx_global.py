import sqlite3
import os

db_path = "brain.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print(f"Searching for 'POLYX' in database: {db_path}")
for table_name in tables:
    table_name = table_name[0]
    print(f"\nChecking table: {table_name}")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    for col in columns:
        try:
            cursor.execute(f"SELECT * FROM {table_name} WHERE CAST({col} AS TEXT) LIKE '%POLYX%'")
            results = cursor.fetchall()
            if results:
                print(f"  Found in column '{col}':")
                for res in results:
                    print(f"    {res}")
        except Exception as e:
            # print(f"  Error checking {table_name}.{col}: {e}")
            pass

conn.close()
