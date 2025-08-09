#!/usr/bin/env python3

import sys
sys.path.append('.')

from app.db.session import SessionLocal
from app.models.organization import Organization
from sqlalchemy import text, select

def test_database_query():
    print("Testing database query directly:")
    db = SessionLocal()
    db.execute(text('SET search_path TO sonicus, public'))
    
    # Test query for testcorp
    print("\n=== Testing 'testcorp' ===")
    stmt = select(Organization).where(
        (Organization.domain == 'testcorp') |
        (Organization.custom_domain == 'testcorp')
    ).where(
        Organization.subscription_status.in_(['trial', 'active'])
    )
    
    result = db.execute(stmt)
    orgs = result.scalars().all()
    
    print(f"Found {len(orgs)} organizations for 'testcorp'")
    for org in orgs:
        print(f"  - {org.name}: domain='{org.domain}' custom_domain='{org.custom_domain}' (status: {org.subscription_status})")
    
    # Test query for testcompany.sonicus.eu
    print("\n=== Testing 'testcompany.sonicus.eu' ===")
    stmt2 = select(Organization).where(
        (Organization.domain == 'testcompany.sonicus.eu') |
        (Organization.custom_domain == 'testcompany.sonicus.eu')
    ).where(
        Organization.subscription_status.in_(['trial', 'active'])
    )
    
    result2 = db.execute(stmt2)
    orgs2 = result2.scalars().all()
    
    print(f"Found {len(orgs2)} organizations for 'testcompany.sonicus.eu'")
    for org in orgs2:
        print(f"  - {org.name}: domain='{org.domain}' custom_domain='{org.custom_domain}' (status: {org.subscription_status})")
    
    # List all organizations
    print("\n=== All Organizations ===")
    all_orgs = db.query(Organization).all()
    for org in all_orgs:
        print(f"  - {org.name}: domain='{org.domain}' custom_domain='{org.custom_domain}' (status: {org.subscription_status})")
    
    db.close()

if __name__ == "__main__":
    test_database_query()
