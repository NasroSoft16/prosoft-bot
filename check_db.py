import sqlite3
import os

db_path = r"c:\Users\dell\Desktop\BINANCE FINAL\PROSOFT_DIST\brain.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trade_memory ORDER BY id DESC LIMIT 5;")
    rows = cursor.fetchall()
    
    # Get column names
    names = [description[0] for description in cursor.description]
    print(" | ".join(names))
    print("-" * 50)
    for row in rows:
        print(row)
    conn.close()
else:
    print(f"Database not found at {db_path}")
