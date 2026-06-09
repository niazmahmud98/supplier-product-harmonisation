import os
from sqlalchemy import text
from models import engine

def inspect_database_tables():
    print("============================================================")
    print("🔍 INVESTIGATING LIVE GCP POSTGRESQL TABLES...")
    print("============================================================")
    
    # Query to fetch all user-defined tables in the public schema of PostgreSQL
    query = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(query)
            tables = [row[0] for row in result.fetchall()]
            
        if tables:
            print(f"🎉 Success! Found {len(tables)} existing table(s) in the database:")
            for idx, table in enumerate(tables, 1):
                print(f"   {idx}. 📋 {table}")
        else:
            print("📭 The database is completely BLANK! No tables found in the 'public' schema.")
            print("ℹ️ This confirms Ryan needs to either run the migration or grant table creation rights.")
            
    except Exception as e:
        print(f"❌ Connection or Permission Error: {e}")
    print("============================================================")

if __name__ == "__main__":
    inspect_database_tables()