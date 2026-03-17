import sqlite3
import os

db_path = "brain.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Checking for POLYX in trade_memory...")
cursor.execute("SELECT * FROM trade_memory WHERE symbol LIKE '%POLYX%'")
trades = cursor.fetchall()
print(f"Found {len(trades)} trades.")
for t in trades:
    print(t)

print("\nChecking for POLYX in revenue_memory...")
cursor.execute("SELECT * FROM revenue_memory WHERE asset LIKE '%POLYX%'")
revenues = cursor.fetchall()
print(f"Found {len(revenues)} revenue records.")
for r in revenues:
    print(r)

conn.close()
