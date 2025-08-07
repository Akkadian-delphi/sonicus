# Sonicus Docker Setup

This directory contains Docker configuration for running the Sonicus application with PostgreSQL and Redis.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Port 18100, 5433, and 6379 available on your host

### Start Database Services Only
If you want to run the backend locally but use Docker for databases:

```bash
./docker-manager.sh db-only
```

This starts:
- PostgreSQL on port 5433
- Redis on port 6379

Then run your backend locally:
```bash
cd backend
python3 run.py
```

### Start All Services (including backend)
```bash
./docker-manager.sh up
```

This starts:
- PostgreSQL on port 5433
- Redis on port 6379  
- Backend API on port 18100

## Management Commands

```bash
# Start all services
./docker-manager.sh up

# Start only databases
./docker-manager.sh db-only

# Stop all services
./docker-manager.sh down

# Restart all services
./docker-manager.sh restart

# View logs
./docker-manager.sh logs

# Check service status
./docker-manager.sh status

# Build backend image
./docker-manager.sh build

# Open backend shell
./docker-manager.sh shell

# Open PostgreSQL shell
./docker-manager.sh db-shell

# Open Redis CLI
./docker-manager.sh redis-cli

# Clean everything (deletes data!)
./docker-manager.sh clean
```

## Access Points

When services are running:

- **Backend API**: http://localhost:18100
- **API Documentation**: http://localhost:18100/docs
- **Health Check**: http://localhost:18100/health
- **PostgreSQL**: `localhost:5433`
- **Redis**: `localhost:6379`

## Database Connection

### From Local Backend
```env
POSTGRES_SERVER=localhost
POSTGRES_PORT=5433
DATABASE_URL=postgresql+asyncpg://postgres:e1efefe@localhost:5433/sonicus_db?options=-csearch_path%3Dsonicus
```

### From Docker Backend
```env
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://postgres:e1efefe@postgres:5432/sonicus_db?options=-csearch_path%3Dsonicus
```

## Development Workflow

### Option 1: Databases in Docker, Backend Local
1. Start databases: `./docker-manager.sh db-only`
2. Run backend locally: `cd backend && python3 run.py`
3. Backend connects to Docker databases on localhost:5433 and localhost:6379

### Option 2: Everything in Docker
1. Start all services: `./docker-manager.sh up`
2. Backend runs in container and connects to Docker databases
3. Access API at http://localhost:18100

## Configuration Files

- `docker-compose.yml` - Main Docker Compose configuration
- `backend/Dockerfile` - Backend container configuration  
- `backend/.env.docker` - Environment variables for Docker
- `backend/docker-init.sql` - PostgreSQL initialization script
- `docker-manager.sh` - Management script

## Troubleshooting

### Port Conflicts
If ports 18100, 5433, or 6379 are in use:
1. Stop conflicting services
2. Or modify ports in `docker-compose.yml`

### Database Connection Issues
1. Ensure containers are healthy: `./docker-manager.sh status`
2. Check logs: `./docker-manager.sh logs`
3. Test PostgreSQL: `./docker-manager.sh db-shell`

### Reset Everything
```bash
./docker-manager.sh clean  # Warning: deletes all data!
./docker-manager.sh up
```
