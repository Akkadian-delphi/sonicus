#!/bin/bash

# Authentik Setup Helper Script for Sonicus Platform
# This script helps you quickly set up the Authentik integration

set -e

echo "🎯 Authentik Setup Helper for Sonicus Platform"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    echo "Please make sure you're running this script from the project root directory."
    exit 1
fi

print_status ".env file found"

# Check if Authentik configuration exists in .env
if grep -q "AUTHENTIK_BASE_URL" .env; then
    print_status "Authentik configuration found in .env"
else
    print_warning "Authentik configuration not found in .env"
    echo "Adding Authentik configuration template..."
    
    cat >> .env << 'EOF'

# Authentik Configuration
AUTHENTIK_BASE_URL=https://authentik.elefefe.eu
AUTHENTIK_CLIENT_ID=your-client-id-here
AUTHENTIK_CLIENT_SECRET=your-client-secret-here
AUTHENTIK_REDIRECT_URI=http://localhost:3000/auth/callback
EOF
    
    print_status "Authentik configuration template added to .env"
fi

# Install required Python packages
print_info "Installing required Python packages..."

if command -v pip &> /dev/null; then
    pip install httpx python-dotenv
    print_status "Required packages installed"
else
    print_error "pip not found. Please install Python packages manually:"
    echo "  pip install httpx python-dotenv"
fi

# Check if Authentik setup guide exists
if [ -f "AUTHENTIK_SETUP_GUIDE.md" ]; then
    print_status "Authentik setup guide available"
else
    print_warning "Authentik setup guide not found"
fi

echo ""
print_info "Next Steps:"
echo "1. 📖 Read the AUTHENTIK_SETUP_GUIDE.md for detailed setup instructions"
echo "2. 🔧 Configure your Authentik server at https://authentik.elefefe.eu"
echo "3. ✏️  Update the .env file with your actual client credentials"
echo "4. 🧪 Run the validation script:"
echo "   python scripts/validate_authentik_config.py"
echo "5. 🚀 Start your application and test the authentication flow"

echo ""
print_status "Setup helper completed!"

# Ask if user wants to open the setup guide
if command -v code &> /dev/null; then
    echo ""
    read -p "Would you like to open the setup guide in VS Code? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        code AUTHENTIK_SETUP_GUIDE.md
        print_status "Setup guide opened in VS Code"
    fi
fi
