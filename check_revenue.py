import sqlite3
import os

db_path = "brain.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- revenue_memory Content ---")
cursor.execute("SELECT * FROM revenue_memory")
rows = cursor.fetchall()
for r in rows:
    print(r)

conn.close()
