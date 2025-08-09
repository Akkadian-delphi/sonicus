#!/usr/bin/env python3
"""
Initialize database with all required tables.
"""
import sys
from pathlib import Path
import os

# Add project root to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Set environment before importing app modules
os.environ.setdefault('ENVIRONMENT', 'development')

try:
    from app.core.config import settings
    from app.db.base import Base
    from sqlalchemy import create_engine
    
    # Import all models to register them with Base.metadata
    from app.models.user import User
    from app.models.organization import Organization, OrganizationSoundPackage, OrganizationAnalytics
    from app.models.subscription import Subscription
    from app.models.invoice import Invoice
    from app.models.therapy_sound import TherapySound
    from app.models.sound_package import SoundPackage
    from app.models.user_session import UserSession
    
    print(f"Using database URL: {settings.DATABASE_URL}")
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
    
    print("\nTables created:")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    for table_name in inspector.get_table_names():
        print(f"  - {table_name}")
    
    print("\n🎉 Database initialization complete!")
    
except Exception as e:
    print(f"❌ Error initializing database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
