#!/usr/bin/env python3
"""Examine Samsung blockchain database"""
import sqlite3
import os

db_path = r"C:\Users\J Ivan\Desktop\SAMSUNG_WALLET_EXTRACTED\blockchain_database.db"

print(f"Opening: {db_path}")
print(f"Size: {os.path.getsize(db_path)} bytes")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"\nTables: {tables}")

# Dump each table
for table in tables:
    print(f"\n{'='*50}")
    print(f"TABLE: {table}")
    print('='*50)
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cursor.fetchall()]
    print(f"Columns: {cols}")
    
    cursor.execute(f"SELECT * FROM {table} LIMIT 10")
    rows = cursor.fetchall()
    print(f"Rows: {len(rows)}")
    for row in rows:
        print(f"  {row}")

conn.close()
