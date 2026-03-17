import sqlite3
import os

db_path = "brain.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Data cleanup started ---")

# 1. Delete from trade_memory
cursor.execute("DELETE FROM trade_memory WHERE symbol LIKE '%POLYX%'")
trades_deleted = cursor.rowcount
print(f"Deleted {trades_deleted} records from trade_memory (POLYX).")

# 2. Delete from revenue_memory
cursor.execute("DELETE FROM revenue_memory WHERE asset LIKE '%POLYX%'")
revenues_deleted = cursor.rowcount
print(f"Deleted {revenues_deleted} records from revenue_memory (POLYX).")

conn.commit()
print("--- Cleanup committed successfully ---")
conn.close()
