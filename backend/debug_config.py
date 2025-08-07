#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/luis/Projects/Elefefe/Sonicus/backend')

from dotenv import load_dotenv
load_dotenv()

print("=== Environment Variables ===")
print(f"POSTGRES_PORT: {os.getenv('POSTGRES_PORT')}")
print(f"POSTGRES_SERVER: {os.getenv('POSTGRES_SERVER')}")
print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER')}")
print(f"POSTGRES_PASSWORD: {'***' if os.getenv('POSTGRES_PASSWORD') else 'None'}")
print(f"POSTGRES_DB: {os.getenv('POSTGRES_DB')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

print("\n=== Settings Object ===")
try:
    from app.core.config import settings
    print(f"settings.POSTGRES_PORT: {settings.POSTGRES_PORT}")
    print(f"settings.POSTGRES_SERVER: {settings.POSTGRES_SERVER}")
    print(f"settings.DATABASE_URL: {settings.DATABASE_URL}")
except Exception as e:
    print(f"Error loading settings: {e}")

print("\n=== Database Session ===")
try:
    from app.db.session import engine
    print(f"Engine URL: {engine.url}")
except Exception as e:
    print(f"Error loading engine: {e}")
