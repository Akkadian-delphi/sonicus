#!/usr/bin/env python3

import sys
sys.path.append('.')
import re
from app.db.session import SessionLocal
from app.models.organization import Organization
from sqlalchemy import text, select

def test_subdomain_extraction():
    """Test subdomain extraction logic similar to tenant middleware"""
    
    # Simulate the subdomain pattern from tenant middleware
    subdomain_pattern = re.compile(r'^([a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.sonicus\.eu$')
    
    test_hosts = [
        "testcompany.sonicus.eu",
        "testcorp.sonicus.eu", 
        "www.sonicus.eu",
        "sonicus.eu",
        "localhost"
    ]
    
    print("=== Subdomain Extraction Test ===")
    for host in test_hosts:
        if host.endswith('.sonicus.eu'):
            match = subdomain_pattern.match(host)
            if match:
                subdomain = match.group(1).lower()
                print(f"{host} -> subdomain: '{subdomain}'")
            else:
                print(f"{host} -> no subdomain match")
        else:
            print(f"{host} -> not a .sonicus.eu domain")

def test_tenant_lookup():
    """Test tenant lookup in database"""
    print("\n=== Tenant Lookup Test ===")
    
    db = SessionLocal()
    db.execute(text('SET search_path TO sonicus, public'))
    
    test_subdomains = ["testcompany", "testcorp", "nonexistent"]
    
    for subdomain in test_subdomains:
        print(f"\nLooking up: '{subdomain}'")
        
        # Simulate the fixed tenant middleware query
        stmt = select(Organization).where(
            (Organization.domain == subdomain) |
            (Organization.custom_domain == subdomain)
        ).where(
            Organization.subscription_status.in_(['trial', 'active'])
        )
        
        result = db.execute(stmt)
        organization = result.scalar_one_or_none()
        
        if organization:
            print(f"  ✓ Found: {organization.name} (status: {organization.subscription_status})")
        else:
            print(f"  ✗ Not found")
    
    db.close()

if __name__ == "__main__":
    test_subdomain_extraction()
    test_tenant_lookup()
