import sqlite3
import os

db_path = "brain.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Checking trade_memory ---")
cursor.execute("SELECT id, symbol, profit_loss, entry_time FROM trade_memory WHERE symbol LIKE '%POLYX%'")
trades = cursor.fetchall()
for t in trades:
    print(t)

print("\n--- Checking revenue_memory ---")
cursor.execute("SELECT id, asset, amount, timestamp FROM revenue_memory WHERE asset LIKE '%POLYX%'")
revenues = cursor.fetchall()
for r in revenues:
    print(r)

conn.close()
