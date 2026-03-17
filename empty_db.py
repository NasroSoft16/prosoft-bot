import sqlite3
import os

db_path = "brain.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Proceeding to empty trade_memory and revenue_memory to avoid any fake profit issues...")

# 1. Empty trade_memory
cursor.execute("DELETE FROM trade_memory")
trades_deleted = cursor.rowcount
print(f"Cleared all {trades_deleted} records from trade_memory.")

# 2. Empty revenue_memory
cursor.execute("DELETE FROM revenue_memory")
revenues_deleted = cursor.rowcount
print(f"Cleared all {revenues_deleted} records from revenue_memory.")

# 3. Optional: Reset vacuum/optimization
cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('trade_memory', 'revenue_memory')")
print("Reset database sequences for clean start.")

conn.commit()
conn.close()

print("\n--- DATABASE CLEANUP COMPLETE ---")
print("All historical trading and revenue data has been cleared as requested.")
