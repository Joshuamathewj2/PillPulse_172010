import os
import psycopg2

try:
    # Try connecting to default postgres database to see if server is running and password works
    conn = psycopg2.connect("postgresql://postgres:Josh$tarj2@localhost:5432/postgres")
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check if pillpulse exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname='pillpulse'")
    if not cur.fetchone():
        print("Database 'pillpulse' missing. Creating it now...")
        cur.execute("CREATE DATABASE pillpulse")
        print("Database 'pillpulse' created successfully!")
    else:
        print("Database 'pillpulse' already exists.")
        
    conn.close()
    print("Database connection and setup successful.")
except Exception as e:
    print(f"Error connecting to database: {e}")
