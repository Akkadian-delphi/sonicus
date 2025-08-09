"""
Configuration validation and setup script for Sonicus Multi-tenant Platform
Validates environment variables and external service connectivity
"""

import os
import asyncio
import logging
import sys
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
import json

try:
    import aiohttp
except ImportError:
    aiohttp = None

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigurationValidator:
    """Validates and sets up Sonicus platform configuration"""
    
    def __init__(self):
        self.validation_results = {}
        self.critical_errors = []
        self.warnings = []
        
    def validate_required_env_vars(self) -> Dict[str, bool]:
        """Validate required environment variables"""
        required_vars = {
            # Core application
            'SECRET_KEY': 'Application secret key for session security',
            'DATABASE_URL': 'PostgreSQL database connection string',
            
            # Redis
            'REDIS_URL': 'Redis connection for caching and sessions',
            
            # JWT
            'JWT_SECRET_KEY': 'JWT token signing secret',
            
            # External services (optional with fallbacks)
            'IONOS_API_KEY': 'IONOS DNS API key (optional, will use mock mode)',
            'REVOLUT_API_KEY': 'Revolut Business API key (optional, will use mock mode)',
            'ODOO_URL': 'Odoo CRM instance URL (optional, will use mock mode)',
            'DEPLOYMENT_WEBHOOK_URL': 'Container deployment webhook URL (optional, will use mock mode)',
        }
        
        results = {}
        
        print("🔍 Validating Environment Variables")
        print("=" * 50)
        
        for var, description in required_vars.items():
            value = os.getenv(var)
            
            if var in ['SECRET_KEY', 'DATABASE_URL', 'REDIS_URL', 'JWT_SECRET_KEY']:
                # Critical variables
                if not value or value.startswith('your-') or value == 'placeholder':
                    results[var] = False
                    self.critical_errors.append(f"❌ {var}: {description} - REQUIRED")
                    print(f"❌ {var}: Missing or placeholder value")
                else:
                    results[var] = True
                    print(f"✅ {var}: Configured")
            else:
                # Optional variables with mock fallback
                if not value or value.startswith('your-') or value == 'placeholder':
                    results[var] = False
                    self.warnings.append(f"⚠️  {var}: {description} - Will use mock mode")
                    print(f"⚠️  {var}: Will use mock mode")
                else:
                    results[var] = True
                    print(f"✅ {var}: Configured")
        
        return results
    
    def validate_database_connection(self) -> bool:
        """Validate database connectivity"""
        print("\n🗄️  Validating Database Connection")
        print("=" * 50)
        
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                print("❌ No database URL configured")
                return False
            
            # Parse database URL
            parsed = urlparse(db_url)
            
            # Test connection
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:] if parsed.path else 'postgres',
                user=parsed.username,
                password=parsed.password
            )
            
            # Test query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            result = cursor.fetchone()
            
            if result:
                version = result[0]
                print(f"✅ Database connection successful")
                print(f"   PostgreSQL version: {version.split(' ')[1]}")
            else:
                print("✅ Database connection successful")
                print("   PostgreSQL version: Unknown")
            
            cursor.close()
            conn.close()
            return True
            
        except ImportError:
            print("⚠️  psycopg2 not installed, skipping database test")
            return False
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.critical_errors.append(f"Database connection failed: {e}")
            return False
    
    async def validate_redis_connection(self) -> bool:
        """Validate Redis connectivity"""
        print("\n🔴 Validating Redis Connection")
        print("=" * 50)
        
        try:
            import redis.asyncio as redis
            
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            
            client = redis.from_url(redis_url)
            
            # Test connection
            await client.ping()
            
            # Test set/get
            await client.set('test_key', 'test_value', ex=10)
            value = await client.get('test_key')
            
            await client.delete('test_key')
            await client.close()
            
            if value == b'test_value':
                print("✅ Redis connection successful")
                print(f"   Connected to: {redis_url}")
                return True
            else:
                print("❌ Redis test operation failed")
                return False
                
        except ImportError:
            print("⚠️  redis not installed, skipping Redis test")
            return False
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self.critical_errors.append(f"Redis connection failed: {e}")
            return False
    
    async def validate_external_services(self) -> Dict[str, bool]:
        """Validate external service connectivity"""
        print("\n🌐 Validating External Service APIs")
        print("=" * 50)
        
        services = {
            'IONOS DNS': {
                'url': 'https://api.hosting.ionos.com',
                'endpoint': '/',
                'api_key': os.getenv('IONOS_API_KEY')
            },
            'Revolut Business': {
                'url': 'https://business-api.revolut.com',
                'endpoint': '/healthcheck',
                'api_key': os.getenv('REVOLUT_API_KEY')
            },
            'Odoo CRM': {
                'url': os.getenv('ODOO_URL', ''),
                'endpoint': '/web/health',
                'api_key': 'configured' if os.getenv('ODOO_USERNAME') else None
            }
        }
        
        results = {}
        
        if not aiohttp:
            print("⚠️  aiohttp not installed, skipping external service tests")
            for service_name in services.keys():
                results[service_name] = False
            return results
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for service_name, config in services.items():
                if not config['url'] or config['url'].startswith('https://your-'):
                    print(f"⚠️  {service_name}: Mock mode (no URL configured)")
                    results[service_name] = False
                    continue
                
                try:
                    headers = {}
                    if config['api_key'] and not config['api_key'].startswith('your-'):
                        headers['Authorization'] = f'Bearer {config["api_key"]}'
                    
                    async with session.get(
                        f"{config['url']}{config['endpoint']}",
                        headers=headers
                    ) as response:
                        if response.status < 400:
                            print(f"✅ {service_name}: API accessible")
                            results[service_name] = True
                        else:
                            print(f"⚠️  {service_name}: API returned {response.status}")
                            results[service_name] = False
                
                except Exception as e:
                    print(f"⚠️  {service_name}: {str(e)[:50]}...")
                    results[service_name] = False
        
        return results
    
    def generate_mock_env_file(self) -> None:
        """Generate a working .env file with mock values for development"""
        print("\n📝 Generating Development Environment File")
        print("=" * 50)
        
        env_content = """# Sonicus Development Environment Configuration
# Generated automatically - modify as needed
# ============================================

# Core Application Settings
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production-please-make-it-long-and-random
DATABASE_URL=postgresql://sonicus_user:sonicus_pass@localhost:5432/sonicus_dev
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
JWT_SECRET_KEY=dev-jwt-secret-change-in-production-make-it-different-from-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Development Mode (enables mock responses for external services)
MOCK_MODE=True
TESTING=False

# IONOS DNS Configuration (Mock Mode - will not make real API calls)
IONOS_DNS_API_URL=https://api.hosting.ionos.com/dns/v1
IONOS_API_KEY=mock-ionos-api-key
IONOS_DNS_ZONE_ID=mock-zone-id
IONOS_DOMAIN=sonicus.eu
IONOS_DEFAULT_IP=127.0.0.1

# DNS Verification Settings
DNS_VERIFICATION_TIMEOUT=30
DNS_VERIFICATION_MAX_RETRIES=3
DNS_VERIFICATION_DELAY_SECONDS=2

# Revolut Business API (Mock Mode)
REVOLUT_API_BASE_URL=https://business-api.revolut.com
REVOLUT_SANDBOX_URL=https://sandbox-b2b.revolut.com/api/1.0
REVOLUT_API_KEY=mock-revolut-api-key
REVOLUT_WEBHOOK_SECRET=mock-webhook-secret
REVOLUT_ENVIRONMENT=sandbox

# Odoo CRM Integration (Mock Mode)
ODOO_URL=https://mock-odoo-instance.com
ODOO_DATABASE=mock_database
ODOO_USERNAME=mock_user@example.com
ODOO_PASSWORD=mock_password
ODOO_LEAD_SOURCE=sonicus_registration

# Container Deployment Service (Mock Mode)
DEPLOYMENT_WEBHOOK_URL=https://mock-deployment-service.com/webhook
DEPLOYMENT_WEBHOOK_SECRET=mock-deployment-secret
DEPLOYMENT_SERVICE_AUTH_TOKEN=mock-auth-token

# Email Configuration (Development)
SMTP_SERVER=localhost
SMTP_PORT=1025
SMTP_USERNAME=dev
SMTP_PASSWORD=dev
SMTP_USE_TLS=False

# Admin Contacts
ADMIN_EMAIL=admin@localhost
BILLING_EMAIL=billing@localhost
SUPPORT_EMAIL=support@localhost

# Security Settings (Development)
RATE_LIMIT_PER_MINUTE=1000
RATE_LIMIT_BURST=100
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=lax

# Theme Management
THEME_ASSETS_PATH=./themes
DEFAULT_THEME=professional_blue
THEME_CACHE_TTL=3600

# File Uploads
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_EXTENSIONS=jpg,jpeg,png,gif,pdf,doc,docx
UPLOAD_PATH=./uploads

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log
ENABLE_STRUCTURED_LOGGING=True

# Organization Settings
MIN_SUBDOMAIN_LENGTH=3
MAX_SUBDOMAIN_LENGTH=63
RESERVED_SUBDOMAINS=www,api,admin,mail,ftp,blog,shop,app,mobile,staging,dev,test

# Development URLs
FRONTEND_DEV_URL=http://localhost:3000
BACKEND_DEV_URL=http://localhost:8000
API_BASE_PATH=/api/v1
"""
        
        env_file_path = os.path.join(os.path.dirname(__file__), '..', '.env.dev')
        
        with open(env_file_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Development environment file created: {env_file_path}")
        print("   This file contains mock values for all external services.")
        print("   Copy to .env and modify for your actual environment.")
    
    def print_configuration_summary(self) -> None:
        """Print configuration summary and recommendations"""
        print("\n📋 Configuration Summary")
        print("=" * 70)
        
        if self.critical_errors:
            print("\n❌ Critical Issues (Must Fix):")
            for error in self.critical_errors:
                print(f"   {error}")
        
        if self.warnings:
            print("\n⚠️  Warnings (Optional for Development):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        print("\n📚 Next Steps:")
        print("=" * 30)
        
        if self.critical_errors:
            print("1. 🔧 Fix critical configuration issues above")
            print("2. 📝 Use the generated .env.dev file as a starting point")
            print("3. 🗄️  Set up PostgreSQL and Redis locally")
            print("4. 🔄 Re-run this validator")
        else:
            print("1. ✅ Core configuration is valid!")
            print("2. 🌐 Configure external service APIs for production")
            print("3. 🧪 Run the test suite: python scripts/test_dns_services.py")
            print("4. 🚀 Start the development server")
        
        print("\n🔧 Quick Setup Commands:")
        print("=" * 30)
        print("# Install PostgreSQL (macOS)")
        print("brew install postgresql")
        print("brew services start postgresql")
        print("createdb sonicus_dev")
        print("")
        print("# Install Redis (macOS)")
        print("brew install redis")
        print("brew services start redis")
        print("")
        print("# Create database user")
        print("psql sonicus_dev -c \"CREATE USER sonicus_user WITH PASSWORD 'sonicus_pass';\"")
        print("psql sonicus_dev -c \"GRANT ALL PRIVILEGES ON DATABASE sonicus_dev TO sonicus_user;\"")


async def main():
    """Run configuration validation"""
    print("🔧 Sonicus Platform Configuration Validator")
    print("=" * 70)
    
    validator = ConfigurationValidator()
    
    # Validate environment variables
    env_results = validator.validate_required_env_vars()
    
    # Test database connection
    db_result = validator.validate_database_connection()
    
    # Test Redis connection
    redis_result = await validator.validate_redis_connection()
    
    # Test external services
    service_results = await validator.validate_external_services()
    
    # Generate development environment file if needed
    if validator.critical_errors or not os.path.exists(os.path.join(os.path.dirname(__file__), '..', '.env')):
        validator.generate_mock_env_file()
    
    # Print summary
    validator.print_configuration_summary()
    
    # Return success status
    return len(validator.critical_errors) == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Configuration validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Configuration validation failed: {e}")
        sys.exit(1)
