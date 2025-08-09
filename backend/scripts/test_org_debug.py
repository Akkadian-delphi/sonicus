#!/usr/bin/env python3
"""
Debug script to test organization model access
"""

from app.db.session import get_db
from app.models.organization import Organization
from sqlalchemy import select, text
import traceback

def test_organization_access():
    print("Testing organization model access...")
    
    session = next(get_db())
    try:
        # Test 1: Basic schema info
        result = session.execute(text('SELECT current_schema()'))
        print(f'Current schema: {result.scalar()}')
        
        result = session.execute(text('SHOW search_path'))
        print(f'Search path: {result.scalar()}')
        
        # Test 2: Direct table access
        result = session.execute(text('SELECT COUNT(*) FROM sonicus.organizations'))
        print(f'Direct count (sonicus.organizations): {result.scalar()}')
        
        result = session.execute(text('SELECT COUNT(*) FROM organizations'))
        print(f'Direct count (organizations): {result.scalar()}')
        
        # Test 3: SQLAlchemy model
        stmt = select(Organization).limit(1)
        result = session.execute(stmt)
        org = result.scalar_one_or_none()
        print(f'SQLAlchemy model test: {org}')
        
        # Test 4: The exact query from the error
        print("\nTesting the exact query from registration...")
        stmt = select(Organization).where(
            (Organization.domain == 'testcorp') |
            (Organization.custom_domain == 'testcorp.sonicus.com')
        )
        result = session.execute(stmt)
        existing_org = result.scalar_one_or_none()
        print(f'Registration query test: {existing_org}')
        
    except Exception as e:
        print(f'Error: {e}')
        traceback.print_exc()
    
    session.close()

if __name__ == "__main__":
    test_organization_access()
