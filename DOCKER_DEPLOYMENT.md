# Docker Deployment Guide

This guide explains how to deploy the Team Trip Expense Tracker using Docker.

## Prerequisites

- Docker installed (version 20.10 or higher)
- Docker Compose installed (version 1.29 or higher)

## Project Structure

```
learningproject/
├── Dockerfile              # Backend Docker image definition
├── docker-compose.yml      # Docker Compose orchestration
├── .dockerignore          # Files to exclude from Docker build
├── app/                   # FastAPI application
├── requirements.txt       # Python dependencies
└── data/                  # SQLite database volume (created automatically)
```

## Quick Start

### 1. Build and Run with Docker Compose

From the project root directory:

```powershell
# Build and start the services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (deletes database)
docker-compose down -v
```

### 2. Access the Application

Once running:

- **API Base URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Build and Run Manually

### Build the Docker Image

```powershell
docker build -t expense-tracker-backend .
```

### Run the Container

```powershell
docker run -d `
  --name expense-tracker-backend `
  -p 8000:8000 `
  -v ${PWD}/data:/app/data `
  expense-tracker-backend
```

### Check Container Status

```powershell
# View running containers
docker ps

# View logs
docker logs expense-tracker-backend

# Follow logs
docker logs -f expense-tracker-backend
```

### Stop the Container

```powershell
docker stop expense-tracker-backend
docker rm expense-tracker-backend
```

## Configuration

### Environment Variables

The following environment variables can be configured:

- `DATABASE_URL`: SQLite database file path (default: `sqlite:///./data/expense_tracker.db`)

Example with custom database path:

```powershell
docker run -d `
  --name expense-tracker-backend `
  -p 8000:8000 `
  -e DATABASE_URL=sqlite:///./data/custom_db.db `
  -v ${PWD}/data:/app/data `
  expense-tracker-backend
```

### Ports

The backend service exposes port `8000`. You can map it to a different host port:

```powershell
# Map to port 9000 on host
docker run -d -p 9000:8000 expense-tracker-backend
```

## Data Persistence

The SQLite database is stored in a Docker volume mounted at `/app/data` inside the container.

- **Local directory**: `./data/` (created automatically)
- **Container path**: `/app/data/`
- **Database file**: `expense_tracker.db`

This ensures data persists even when containers are stopped or removed.

### Backup the Database

```powershell
# Copy database from container
docker cp expense-tracker-backend:/app/data/expense_tracker.db ./backup.db
```

### Restore the Database

```powershell
# Copy database to container
docker cp ./backup.db expense-tracker-backend:/app/data/expense_tracker.db

# Restart container to apply changes
docker restart expense-tracker-backend
```

## Health Checks

The container includes a health check that pings the `/health` endpoint every 30 seconds.

Check health status:

```powershell
docker inspect --format='{{.State.Health.Status}}' expense-tracker-backend
```

## Production Deployment

For production deployments, consider:

1. **Use a production WSGI server** (already using uvicorn in production mode)
2. **Add HTTPS** with a reverse proxy (nginx, traefik, or Caddy)
3. **Set up proper logging** with log aggregation
4. **Use PostgreSQL** instead of SQLite for better concurrency
5. **Add CORS middleware** if frontend is on a different domain
6. **Enable rate limiting** to prevent abuse
7. **Set resource limits** in docker-compose.yml

### Example with Resource Limits

Update `docker-compose.yml`:

```yaml
services:
  backend:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

## Troubleshooting

### Container Won't Start

Check logs:

```powershell
docker-compose logs backend
```

### Port Already in Use

If port 8000 is already in use, change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Maps host port 8001 to container port 8000
```

### Database Permission Issues

Ensure the `data/` directory has proper permissions:

```powershell
# Windows (run as administrator if needed)
mkdir data
icacls data /grant Users:F
```

### Cannot Connect to API

1. Check if container is running: `docker ps`
2. Check health status: `docker inspect --format='{{.State.Health.Status}}' expense-tracker-backend`
3. Test health endpoint: `curl http://localhost:8000/health`
4. Check firewall settings

## Development vs Production

### Development Mode

Use the current setup with:
- SQLite database
- Local volume mounts
- Auto-reload disabled (for stability)

### Production Mode

Consider:
- Using PostgreSQL with a separate container
- Adding nginx as a reverse proxy
- Using Docker secrets for sensitive data
- Implementing proper backup strategies

Example with PostgreSQL (future enhancement):

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: expense_tracker
      POSTGRES_USER: expense_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://expense_user:secure_password@db:5432/expense_tracker
```

## Next Steps

1. Test the deployment: `docker-compose up -d`
2. Verify API access: http://localhost:8000/docs
3. Create a test trip using the Swagger UI
4. Check database persistence by restarting: `docker-compose restart`
5. Review logs for any errors: `docker-compose logs -f

## Cleanup

Remove all containers, images, and volumes:

```powershell
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes database)
docker-compose down -v

# Remove the built image
docker rmi expense-tracker-backend
```
