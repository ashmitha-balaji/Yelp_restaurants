#!/usr/bin/env python3
"""
Run this script to test your database connection.
Usage: python test_db.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://yelp_user:yelp_password@localhost:3306/yelp_db")

def test_connection():
    print("Testing database connection...")
    print(f"Using: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('//')[1], '***')}@...")
    print()
    
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful!")
        
        # Check if tables exist
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
        
        if tables:
            print(f"✓ Found {len(tables)} table(s):", ", ".join(tables))
        else:
            print("⚠ No tables found. Tables will be created when you start the backend.")
        
        return True
    except Exception as e:
        print("✗ Database connection FAILED!")
        print(f"Error: {e}")
        print()
        print("Common fixes:")
        print("1. Is MySQL running? Try: brew services start mysql  (macOS)")
        print("2. Does the database exist? Run: mysql -u root -p -e 'CREATE DATABASE yelp_db;'")
        print("3. Does the user exist? Run the SQL from reference.txt (CREATE USER, GRANT)")
        print("4. Check your .env file - is DATABASE_URL correct?")
        return False

if __name__ == "__main__":
    test_connection()
