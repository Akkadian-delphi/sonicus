#!/bin/bash

# Sonicus Development Environment Stop Script
# Stops Docker containers and development servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[SONICUS]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_status "Stopping Sonicus Development Environment"
echo "========================================"

# Stop any running development servers
print_status "Stopping development servers..."

# Stop Python backend servers
pkill -f "python.*run.py" 2>/dev/null || true
pkill -f "uvicorn.*run:app" 2>/dev/null || true

# Stop Node.js frontend servers
pkill -f "react-scripts.*start" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true

sleep 2

# Stop Docker containers
if [ -f "docker-compose.dev.yml" ]; then
    print_status "Stopping Docker containers..."
    docker-compose -f docker-compose.dev.yml down
    print_success "Docker containers stopped"
else
    print_status "No docker-compose.dev.yml found, skipping container cleanup"
fi

# Check if any processes are still running on development ports
RUNNING_PROCESSES=$(lsof -i :18100 -i :3000 -i :3001 -i :5432 -i :6379 2>/dev/null | grep LISTEN || true)

if [ -z "$RUNNING_PROCESSES" ]; then
    print_success "All development services stopped"
else
    print_status "Some processes still running on development ports:"
    echo "$RUNNING_PROCESSES"
    echo ""
    echo "You may need to manually stop these processes"
fi

print_success "Development environment cleanup complete"
