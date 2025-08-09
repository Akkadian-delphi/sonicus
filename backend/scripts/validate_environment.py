#!/usr/bin/env python3
"""
Validate that all required environment variables are set for production deployment
"""

import os
import sys

REQUIRED_VARS = [
    'POSTGRES_SERVER',
    'POSTGRES_USER', 
    'POSTGRES_PASSWORD',
    'POSTGRES_DB',
    'SECRET_KEY',
]

RECOMMENDED_VARS = [
    'REDIS_HOST',
    'REDIS_PASSWORD',
    'CORS_ORIGINS',
    'DEBUG',
    'API_V1_STR',
]

def check_environment():
    """Check if all required environment variables are set"""
    missing_required = []
    missing_recommended = []
    
    print("🔍 Checking environment variables...")
    print("=" * 50)
    
    # Check required variables
    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if not value:
            missing_required.append(var)
            print(f"❌ {var}: Missing (REQUIRED)")
        else:
            # Mask sensitive values
            if any(sensitive in var.lower() for sensitive in ['password', 'secret', 'key']):
                display_value = f"{'*' * (len(value) - 4)}{value[-4:]}" if len(value) > 4 else "****"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
    
    print("\n" + "=" * 50)
    
    # Check recommended variables
    for var in RECOMMENDED_VARS:
        value = os.getenv(var)
        if not value:
            missing_recommended.append(var)
            print(f"⚠️  {var}: Missing (Recommended)")
        else:
            if any(sensitive in var.lower() for sensitive in ['password', 'secret', 'key']):
                display_value = f"{'*' * (len(value) - 4)}{value[-4:]}" if len(value) > 4 else "****"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
    
    print("\n" + "=" * 50)
    
    if missing_required:
        print(f"❌ CRITICAL: {len(missing_required)} required variables missing!")
        print("Application will likely fail to start.")
        print(f"Missing: {', '.join(missing_required)}")
        return False
    
    if missing_recommended:
        print(f"⚠️  WARNING: {len(missing_recommended)} recommended variables missing.")
        print(f"Missing: {', '.join(missing_recommended)}")
    
    if not missing_required and not missing_recommended:
        print("🎉 All environment variables are properly configured!")
    
    return True

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
