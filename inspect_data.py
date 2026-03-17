import sqlite3
import os

db_path = "brain.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Distinct Symbols in trade_memory ---")
cursor.execute("SELECT DISTINCT symbol FROM trade_memory")
for row in cursor.fetchall():
    print(row)

print("\n--- Distinct Assets in revenue_memory ---")
cursor.execute("SELECT DISTINCT asset FROM revenue_memory")
for row in cursor.fetchall():
    print(row)

conn.close()
