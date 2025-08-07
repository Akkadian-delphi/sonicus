#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/luis/Projects/Elefefe/Sonicus/backend')

from dotenv import load_dotenv
load_dotenv()

try:
    from app.db.session import engine
    from sqlalchemy import text
    
    print(f"Testing connection with engine URL: {engine.url}")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"✅ Database connection successful!")
        
        # Test schema access
        conn.execute(text("SET search_path TO sonicus, public"))
        print("✅ Schema path set successfully")
        
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print(f"Error type: {type(e).__name__}")
