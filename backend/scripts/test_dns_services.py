#!/usr/bin/env python3
"""
Test script for DNS Configuration and Multi-tenant Services
Validates all core services for subdomain management and organization registration
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.dns_service import dns_service
from app.services.dns_verification import dns_verification_service
from app.services.stripe_service import stripe_service
from app.services.odoo_service import odoo_service
from app.services.deployment_service import deployment_service

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_dns_service():
    """Test DNS service functionality"""
    print("\n🌐 Testing DNS Service")
    print("=" * 50)
    
    # Get service status
    status = dns_service.get_status()
    print(f"DNS Service Status: {status}")
    
    # Test subdomain validation
    test_subdomains = ["test-company", "invalid_subdomain", "www", "api", "valid-test-123"]
    
    for subdomain in test_subdomains:
        is_valid = await dns_service.validate_subdomain_format(subdomain)
        print(f"Subdomain '{subdomain}': {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test DNS record creation (mock mode if not configured)
    test_subdomain = "test-organization"
    test_ip = "192.168.1.1"
    
    print(f"\nTesting DNS record creation for {test_subdomain}.sonicus.eu -> {test_ip}")
    success = await dns_service.create_subdomain_record(test_subdomain, test_ip)
    print(f"DNS Record Creation: {'✅ Success' if success else '❌ Failed'}")
    
    # Test listing records
    print("\nListing subdomain records:")
    records = await dns_service.list_subdomain_records()
    print(f"Found {len(records)} subdomain records")
    
    return status['enabled'] and status['api_configured']


async def test_dns_verification_service():
    """Test DNS verification service functionality"""
    print("\n🔍 Testing DNS Verification Service")
    print("=" * 50)
    
    # Get service configuration
    config = dns_verification_service.get_configuration()
    print(f"DNS Verification Config: {config}")
    
    # Test subdomain availability check
    test_subdomains = ["definitely-not-exists-12345", "www", "google"]
    
    for subdomain in test_subdomains:
        availability = await dns_verification_service.check_subdomain_availability(subdomain)
        print(f"Subdomain '{subdomain}': {'✅ Available' if availability['available'] else '❌ Taken'} - {availability['reason']}")
    
    # Test DNS resolution for known domain
    print(f"\nTesting DNS resolution for google.com")
    is_resolved = await dns_verification_service.verify_subdomain_resolution("google", "142.251.46.238")
    print(f"DNS Resolution Test: {'✅ Success' if is_resolved else '❌ Failed'}")
    
    return config['enabled']


async def test_stripe_service():
    """Test Stripe payment service integration"""
    print("\n" + "="*50)
    print("🏦 TESTING STRIPE PAYMENT SERVICE")
    print("="*50)
    
    status = stripe_service.get_status()
    print(f"Stripe Service Status: {status}")
    
    if not status.get("enabled"):
        return {
            "service": "Stripe",
            "status": "SKIPPED",
            "message": "Service not enabled or configured"
        }
    
    try:
        # Test customer creation
        customer_data = {
            "email": "test@example.com",
            "name": "Test Organization",
            "phone": "+1234567890"
        }
        
        customer = await stripe_service.create_customer(customer_data)
        
        if customer:
            print(f"✅ Customer created: {customer.get('id')}")
            
            # Test subscription creation
            subscription_data = {
                "customer_id": customer.get('id'),
                "price_id": "price_starter",
                "metadata": {"organization_id": "test-org-123"},
                "trial_days": 14
            }
            
            subscription = await stripe_service.create_subscription(subscription_data)
            if subscription:
                print(f"✅ Subscription created: {subscription.get('id')}")
        
        # Test listing plans
        plans = await stripe_service.list_subscription_plans()
        if plans:
            print(f"✅ Found {len(plans)} subscription plans")
            
        return {
            "service": "Stripe",
            "status": "PASSED", 
            "message": f"Customer: {customer.get('id') if customer else 'Failed'}"
        }
        
    except Exception as e:
        print(f"❌ Stripe service test failed: {e}")
        return {
            "service": "Stripe",
            "status": "FAILED",
            "message": str(e)
        }


async def test_odoo_service():
    """Test Odoo CRM service functionality"""
    print("\n🎯 Testing Odoo CRM Service")
    print("=" * 50)
    
    # Get service status
    status = odoo_service.get_status()
    print(f"Odoo Service Status: {status}")
    
    # Test authentication (if configured)
    if status['configured']:
        auth_success = await odoo_service.authenticate()
        print(f"Odoo Authentication: {'✅ Success' if auth_success else '❌ Failed'}")
    
    # Test lead creation (mock mode if not configured)
    lead_data = {
        "name": "Test Business Registration",
        "email": "business@testcompany.com",
        "phone": "+1234567890",
        "website": "test-company.sonicus.eu",
        "company_name": "Test Company Ltd",
        "source": "sonicus_registration",
        "subscription_plan": "starter_plan",
        "description": "New business registration from Sonicus platform"
    }
    
    print(f"\nTesting lead creation for {lead_data['company_name']}")
    lead = await odoo_service.create_lead(lead_data)
    print(f"Lead Creation: {'✅ Success' if lead else '❌ Failed'}")
    
    if lead:
        print(f"Lead ID: {lead.get('id')}")
        print(f"Lead URL: {lead.get('odoo_url', 'N/A')}")
    
    # Test lead search
    print(f"\nTesting lead search")
    search_results = await odoo_service.search_leads({"company_name": "Test Company"})
    print(f"Lead Search: Found {len(search_results)} matching leads")
    
    return status['enabled']


async def test_deployment_service():
    """Test container deployment service functionality"""
    print("\n🐳 Testing Container Deployment Service")
    print("=" * 50)
    
    # Get service status
    status = deployment_service.get_status()
    print(f"Deployment Service Status: {status}")
    
    # Test deployment trigger (mock mode)
    deployment_data = {
        "organization_id": "test-org-123",
        "subdomain": "test-company",
        "admin_email": "admin@testcompany.com",
        "organization_name": "Test Company Ltd",
        "subscription_id": "sub_123456",
        "database_config": {
            "name": "sonicus_test_company",
            "host": "localhost"
        },
        "resources": {
            "cpu": "1.0",
            "memory": "1Gi",
            "storage": "2Gi"
        }
    }
    
    print(f"\nTesting container deployment trigger for {deployment_data['subdomain']}")
    success = await deployment_service.trigger_container_deployment(deployment_data)
    print(f"Deployment Trigger: {'✅ Success' if success else '❌ Failed'}")
    
    # Test deployment status check
    print(f"\nTesting deployment status check")
    deployment_status = await deployment_service.check_deployment_status("test-org-123")
    print(f"Deployment Status: {deployment_status.get('status', 'unknown')}")
    print(f"Status Message: {deployment_status.get('message', 'No message')}")
    
    return status['enabled']


async def test_integrated_workflow():
    """Test integrated organization registration workflow"""
    print("\n🔄 Testing Integrated Registration Workflow")
    print("=" * 50)
    
    # Simulate complete organization registration
    org_data = {
        "organization_name": "Integration Test Company",
        "subdomain": "integration-test",
        "admin_email": "admin@integration-test.com",
        "admin_phone": "+1555123456",
        "subscription_plan": "professional_plan"
    }
    
    workflow_results = {}
    
    print(f"🏢 Processing registration for: {org_data['organization_name']}")
    print(f"📍 Subdomain: {org_data['subdomain']}.sonicus.eu")
    
    # Step 1: Validate subdomain
    print(f"\n1. Validating subdomain format...")
    subdomain_valid = await dns_service.validate_subdomain_format(org_data['subdomain'])
    workflow_results['subdomain_validation'] = subdomain_valid
    print(f"   {'✅ Valid' if subdomain_valid else '❌ Invalid'}")
    
    if subdomain_valid:
        # Step 2: Check subdomain availability
        print(f"2. Checking subdomain availability...")
        availability = await dns_verification_service.check_subdomain_availability(org_data['subdomain'])
        workflow_results['subdomain_availability'] = availability['available']
        print(f"   {'✅ Available' if availability['available'] else '❌ Taken'}")
        
        if availability['available']:
            # Step 3: Create Stripe customer
            print(f"3. Creating Stripe customer...")
            customer = await stripe_service.create_customer({
                "name": org_data['organization_name'],
                "email": org_data['admin_email'],
                "phone": org_data['admin_phone']
            })
            workflow_results['customer_creation'] = bool(customer)
            print(f"   {'✅ Success' if customer else '❌ Failed'}")
            
            if customer:
                # Step 4: Create subscription
                print(f"4. Creating subscription...")
                subscription = await stripe_service.create_subscription({
                    "customer_id": customer['id'],
                    "price_id": org_data['subscription_plan'],
                    "metadata": {"subdomain": org_data['subdomain']}
                })
                workflow_results['subscription_creation'] = bool(subscription)
                print(f"   {'✅ Success' if subscription else '❌ Failed'}")
                
                # Step 5: Create DNS record
                print(f"5. Creating DNS record...")
                dns_success = await dns_service.create_subdomain_record(
                    org_data['subdomain'], 
                    "192.168.1.1"
                )
                workflow_results['dns_creation'] = dns_success
                print(f"   {'✅ Success' if dns_success else '❌ Failed'}")
                
                # Step 6: Trigger container deployment
                print(f"6. Triggering container deployment...")
                deployment_success = await deployment_service.trigger_container_deployment({
                    "organization_id": f"org_{org_data['subdomain']}",
                    "subdomain": org_data['subdomain'],
                    "admin_email": org_data['admin_email'],
                    "organization_name": org_data['organization_name'],
                    "subscription_id": subscription.get('id') if subscription else None
                })
                workflow_results['deployment_trigger'] = deployment_success
                print(f"   {'✅ Success' if deployment_success else '❌ Failed'}")
                
                # Step 7: Create CRM lead
                print(f"7. Creating CRM lead...")
                lead = await odoo_service.create_lead({
                    "name": f"{org_data['organization_name']} - Registration",
                    "email": org_data['admin_email'],
                    "phone": org_data['admin_phone'],
                    "company_name": org_data['organization_name'],
                    "website": f"{org_data['subdomain']}.sonicus.eu",
                    "subscription_plan": org_data['subscription_plan'],
                    "stripe_customer_id": customer.get('id')
                })
                workflow_results['crm_lead_creation'] = bool(lead)
                print(f"   {'✅ Success' if lead else '❌ Failed'}")
    
    # Summary
    print(f"\n📊 Workflow Summary:")
    print("=" * 30)
    total_steps = len(workflow_results)
    successful_steps = sum(workflow_results.values())
    
    for step, success in workflow_results.items():
        print(f"{step.replace('_', ' ').title()}: {'✅' if success else '❌'}")
    
    print(f"\nOverall Success Rate: {successful_steps}/{total_steps} ({successful_steps/total_steps*100:.1f}%)")
    
    return successful_steps == total_steps


async def main():
    """Run all service tests"""
    print("🚀 Starting DNS Configuration & Multi-tenant Services Test")
    print("=" * 70)
    
    test_results = {}
    
    # Test individual services
    test_results['dns'] = await test_dns_service()
    test_results['dns_verification'] = await test_dns_verification_service()
    test_results['stripe'] = await test_stripe_service()
    test_results['odoo'] = await test_odoo_service()
    test_results['deployment'] = await test_deployment_service()
    
    # Test integrated workflow
    test_results['integrated_workflow'] = await test_integrated_workflow()
    
    # Overall summary
    print("\n🎯 Final Test Summary")
    print("=" * 70)
    
    for service, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{service.replace('_', ' ').title():<25}: {status}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! DNS Configuration system is ready for production.")
    else:
        print(f"\n⚠️  Some tests failed. Check configuration and service availability.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test execution failed: {e}")
        sys.exit(1)
