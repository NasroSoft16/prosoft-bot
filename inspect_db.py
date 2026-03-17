import sqlite3
import os

db_path = "brain.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- trade_memory Schema ---")
cursor.execute("PRAGMA table_info(trade_memory)")
for col in cursor.fetchall():
    print(col)

print("\n--- revenue_memory Schema ---")
cursor.execute("PRAGMA table_info(revenue_memory)")
for col in cursor.fetchall():
    print(col)

conn.close()
