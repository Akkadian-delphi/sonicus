#!/bin/bash

# Sonicus Docker Management Script
# This script helps manage the Docker containers for the Sonicus application

set -e

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

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Display usage information
show_usage() {
    echo "Sonicus Docker Management Script"
    echo "================================"
    echo
    echo "Usage: $0 <command>"
    echo
    echo "Commands:"
    echo "  up          Start all services (postgres, redis, backend)"
    echo "  down        Stop all services"
    echo "  restart     Restart all services"
    echo "  logs        Show logs for all services"
    echo "  db-only     Start only database services (postgres, redis)"
    echo "  status      Show status of all services"
    echo "  clean       Stop services and remove volumes (WARNING: deletes data!)"
    echo "  build       Build the backend image"
    echo "  shell       Open a shell in the backend container"
    echo "  db-shell    Open a PostgreSQL shell"
    echo "  redis-cli   Open Redis CLI"
    echo
}

# Main command processing
case "${1:-}" in
    "up")
        check_docker
        print_info "Starting Sonicus services..."
        docker-compose up -d
        print_status "All services started successfully!"
        print_info "Access points:"
        print_info "  - Backend API: http://localhost:18100"
        print_info "  - API Docs: http://localhost:18100/docs"
        print_info "  - PostgreSQL: localhost:5433"
        print_info "  - Redis: localhost:6379"
        ;;
    
    "down")
        check_docker
        print_info "Stopping Sonicus services..."
        docker-compose down
        print_status "All services stopped."
        ;;
    
    "restart")
        check_docker
        print_info "Restarting Sonicus services..."
        docker-compose down
        docker-compose up -d
        print_status "All services restarted successfully!"
        ;;
    
    "logs")
        check_docker
        print_info "Showing logs for all services..."
        docker-compose logs -f
        ;;
    
    "db-only")
        check_docker
        print_info "Starting database services only..."
        docker-compose up -d postgres redis
        print_status "Database services started!"
        print_info "PostgreSQL: localhost:5433"
        print_info "Redis: localhost:6379"
        ;;
    
    "status")
        check_docker
        print_info "Service status:"
        docker-compose ps
        ;;
    
    "clean")
        check_docker
        print_warning "This will stop all services and DELETE all data!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Cleaning up..."
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_status "Cleanup completed."
        else
            print_info "Cleanup cancelled."
        fi
        ;;
    
    "build")
        check_docker
        print_info "Building backend image..."
        docker-compose build backend
        print_status "Backend image built successfully!"
        ;;
    
    "shell")
        check_docker
        print_info "Opening shell in backend container..."
        docker-compose exec backend /bin/bash
        ;;
    
    "db-shell")
        check_docker
        print_info "Opening PostgreSQL shell..."
        docker-compose exec postgres psql -U postgres -d sonicus_db
        ;;
    
    "redis-cli")
        check_docker
        print_info "Opening Redis CLI..."
        docker-compose exec redis redis-cli -a e1efefe
        ;;
    
    *)
        show_usage
        exit 1
        ;;
esac
