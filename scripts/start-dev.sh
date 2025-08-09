#!/bin/bash

# Sonicus Development Environment Setup Script
# Starts Docker containers and validates the development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[SONICUS]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_status "Starting Sonicus Development Environment"
echo "=========================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

print_success "Docker is running"

# Check if we're in the right directory
if [ ! -f "docker-compose.dev.yml" ]; then
    print_error "docker-compose.dev.yml not found. Please run this script from the project root."
    exit 1
fi

# Start Docker containers
print_status "Starting Docker containers..."
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Wait for containers to be healthy
print_status "Waiting for containers to be ready..."

# Wait for PostgreSQL
echo -n "Waiting for PostgreSQL"
for i in {1..30}; do
    if docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U sonicus_user -d sonicus_dev >/dev/null 2>&1; then
        echo ""
        print_success "PostgreSQL is ready"
        break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 30 ]; then
        echo ""
        print_error "PostgreSQL failed to start within 30 seconds"
        exit 1
    fi
done

# Wait for Redis
echo -n "Waiting for Redis"
for i in {1..30}; do
    if docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping >/dev/null 2>&1; then
        echo ""
        print_success "Redis is ready"
        break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 30 ]; then
        echo ""
        print_error "Redis failed to start within 30 seconds"
        exit 1
    fi
done

# Create Python virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

# Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
source .venv/bin/activate

# Install backend dependencies
cd backend
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt >/dev/null 2>&1
else
    pip install -r requirements.txt >/dev/null 2>&1
fi
cd ..

print_success "Python dependencies installed"

# Run database migrations if they exist
print_status "Checking database setup..."

# Check if we have database migration scripts
if [ -f "scripts/setup_database.py" ]; then
    print_status "Running database setup..."
    PYTHONPATH="." python scripts/setup_database.py
elif [ -f "app/db/migrations.py" ]; then
    print_status "Running database migrations..."
    PYTHONPATH="." python -c "from app.db.migrations import create_all_tables; create_all_tables()"
else
    print_warning "No database setup scripts found"
fi

# Validate configuration
if [ -f "scripts/validate_configuration.py" ]; then
    print_status "Validating configuration..."
    PYTHONPATH="." python scripts/validate_configuration.py
    if [ $? -eq 0 ]; then
        print_success "Configuration validation passed"
    else
        print_warning "Configuration validation found issues (check output above)"
    fi
fi

# Check if Node.js dependencies are installed for frontend
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    print_status "Checking frontend dependencies..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm install >/dev/null 2>&1
        print_success "Node.js dependencies installed"
    else
        print_success "Node.js dependencies already installed"
    fi
    cd ..
fi

print_success "Development environment is ready!"
echo ""
echo "🚀 Quick Start Commands:"
echo "========================"
echo "Backend:"
echo "  cd backend && python run.py"
echo ""
echo "Frontend:"
echo "  cd frontend && npm start"
echo ""
echo "🔧 Management Tools (optional):"
echo "================================"
echo "PostgreSQL GUI (pgAdmin): docker-compose -f docker-compose.dev.yml --profile tools up -d pgadmin"
echo "  Access at: http://localhost:8080 (admin@sonicus.dev / admin123)"
echo ""
echo "Redis GUI (Commander): docker-compose -f docker-compose.dev.yml --profile tools up -d redis-commander"
echo "  Access at: http://localhost:8081"
echo ""
echo "🛑 Stop Services:"
echo "=================="
echo "docker-compose -f docker-compose.dev.yml down"
echo ""
echo "📊 Container Status:"
echo "==================="
docker-compose -f docker-compose.dev.yml ps
