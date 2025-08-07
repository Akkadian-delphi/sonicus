#!/usr/bin/env python3
"""
Simple PostgreSQL connection test for Sonicus.
This script tests the database connection using the credentials from .env file.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test PostgreSQL connection with credentials from .env"""
    
    # Get database settings from environment
    db_host = os.getenv("POSTGRES_SERVER", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_name = os.getenv("POSTGRES_DB", "praetoria_db")
    
    print("🔍 Testing PostgreSQL connection...")
    print(f"Host: {db_host}")
    print(f"Port: {db_port}")
    print(f"User: {db_user}")
    print(f"Password: {'*' * len(db_password)}")
    print(f"Database: {db_name}")
    print("-" * 40)
    
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 is not installed. Install it with:")
        print("   pip install psycopg2-binary")
        return False
    
    try:
        # First, try connecting to the default 'postgres' database
        print("Testing connection to default 'postgres' database...")
        conn = psycopg2.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            database="postgres"  # Connect to default postgres db first
        )
        print("✅ Successfully connected to PostgreSQL!")
        
        # Check if our target database exists
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"✅ Database '{db_name}' exists")
            # Try connecting to the target database
            conn.close()
            conn = psycopg2.connect(
                host=db_host,
                port=int(db_port),
                user=db_user,
                password=db_password,
                database=db_name
            )
            print(f"✅ Successfully connected to '{db_name}' database!")
        else:
            print(f"⚠️  Database '{db_name}' does not exist")
            print("Creating database...")
            
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Database '{db_name}' created successfully!")
        
        conn.close()
        print("\n🎉 Database connection test passed!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        
        if "password authentication failed" in str(e):
            print("\n🔧 PASSWORD AUTHENTICATION FAILED:")
            print("1. Check your .env file has the correct POSTGRES_PASSWORD")
            print("2. Reset postgres password:")
            print("   - Connect as superuser: sudo -u postgres psql")
            print("   - Change password: ALTER USER postgres PASSWORD 'new_password';")
            print("3. Or create a new user:")
            print("   - sudo -u postgres createuser --interactive --pwprompt")
            
        elif "connection refused" in str(e):
            print("\n🔧 CONNECTION REFUSED:")
            print("PostgreSQL server is not running. Start it with:")
            print("   - macOS: brew services start postgresql")
            print("   - Linux: sudo systemctl start postgresql")
            print("   - Check status: brew services list | grep postgresql")
            
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_postgres_commands():
    """Show useful PostgreSQL commands"""
    print("\n📋 USEFUL POSTGRESQL COMMANDS:")
    print("Check if PostgreSQL is running:")
    print("  brew services list | grep postgresql")
    print("  ps aux | grep postgres")
    print()
    print("Start PostgreSQL:")
    print("  brew services start postgresql")
    print()
    print("Connect to PostgreSQL:")
    print("  psql -h localhost -U postgres -d postgres")
    print()
    print("List databases:")
    print("  \\l (inside psql)")
    print()
    print("Create database:")
    print("  CREATE DATABASE your_db_name;")

if __name__ == "__main__":
    if not test_connection():
        show_postgres_commands()
        sys.exit(1)
    else:
        print("\n✅ Ready to start Sonicus application!")
        sys.exit(0)
