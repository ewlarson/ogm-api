# Kamal Deployment Guide

This document describes the deployment process for the OGM API using [Kamal](https://kamal-deploy.org/), a modern deployment tool that uses Docker containers.

## Overview

The OGM API is deployed to production using Kamal, which orchestrates Docker containers across servers. The application consists of:

- **Web Service**: FastAPI application (Python/uvicorn)
- **Accessories** (supporting services):
  - PostgreSQL database
  - Elasticsearch search engine
  - Redis cache/message broker

## Prerequisites

### 1. Install Kamal

```bash
gem install kamal
```

Verify installation:
```bash
kamal version
```

### 2. Required Access

- SSH access to the deployment server (`ogm.geo4lib.app`)
- GitHub Container Registry (GHCR) access
- Environment variables for secrets (see Secrets section)

### 3. Server Requirements

- Docker installed on the target server
- SSH key-based authentication configured
- Port access: 80, 443 (web), 9200 (Elasticsearch), 5432 (PostgreSQL), 6379 (Redis)

## Configuration

The deployment configuration is defined in `config/deploy.yml`:

### Service Configuration

```yaml
service: opengeometadata-api
image: ewlarson/opengeometadata-api
```

The application is deployed as the `opengeometadata-api` service with images hosted on GitHub Container Registry.

### Server Configuration

```yaml
servers:
  web:
    hosts:
      - ogm.geo4lib.app
```

Deploys to a single production server at `ogm.geo4lib.app`.

### Proxy & SSL

```yaml
proxy:
  ssl: true
  host: ogm.geo4lib.app
  app_port: 8000
  healthcheck:
    path: /api/docs
```

- Automatic SSL certificate management via Let's Encrypt
- Application runs on port 8000 internally
- Health checks performed against `/api/docs` endpoint

### Container Registry

```yaml
registry:
  server: ghcr.io
  username: ewlarson
  password:
    - KAMAL_REGISTRY_PASSWORD
```

Uses GitHub Container Registry for Docker images.

## Secrets Management

Secrets are managed through `.kamal/secrets` file. **This file should NEVER contain raw credentials.**

### Required Secrets

Add these environment variables to your local shell before deployment:

```bash
# GitHub Container Registry token (required for pulling images)
export KAMAL_REGISTRY_PASSWORD="your_github_token"

# OpenAI API key (for AI features)
export OPENAI_API_KEY="your_openai_key"

# Optional: OpenAI model configuration
export OPENAI_MODEL="gpt-4"
```

### Secret Types in Configuration

The `.kamal/secrets` file references these secrets:

1. **KAMAL_REGISTRY_PASSWORD**: GitHub Container Registry authentication
2. **DATABASE_URL**: PostgreSQL connection string (configured for Docker network)
3. **OPENAI_API_KEY**: OpenAI API access
4. **POSTGRES_PASSWORD**: PostgreSQL database password

## Environment Variables

### Application Environment

These are passed to every web container:

```yaml
env:
  clear:
    ELASTICSEARCH_URL: http://ogm-api-elasticsearch:9200
    REDIS_URL: redis://redis:6379/0
    ELASTICSEARCH_INDEX: opengeometadata_api
    REDIS_TTL: "604800"
    LOG_LEVEL: DEBUG
    ENDPOINT_CACHE: "true"
    GAZETTEER_CACHE_TTL: "3600"
    APP_MODE: production
    APPLICATION_URL: https://ogm.geo4lib.app
  
  secret:
    - DATABASE_URL
    - OPENAI_API_KEY
```

## Accessories

Kamal manages supporting services as "accessories". Each runs in its own container.

### Elasticsearch

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:9.0.0
  env:
    discovery.type: single-node
    xpack.security.enabled: "false"
    ES_JAVA_OPTS: "-Xms2g -Xmx2g"
```

- Single-node configuration
- 2GB heap size
- Security disabled (bound to localhost only)
- Data persisted to `esdata` volume

### PostgreSQL

```yaml
postgres:
  image: postgres:15
  env:
    POSTGRES_USER: ogm_api_user
    POSTGRES_DB: opengeometadata_api
```

- PostgreSQL 15
- Initialization SQL from `config/init.sql`
- Data persisted to `pgdata` volume

### Redis

```yaml
redis:
  image: redis:7.2
  cmd: redis-server --appendonly yes
```

- Redis 7.2
- Append-only file (AOF) persistence enabled
- Data persisted to `redisdata` volume

## Deployment Commands

### Initial Setup

For first-time deployment, set up the server infrastructure:

```bash
# Set up Kamal on the server (creates directories, installs proxy, etc.)
kamal setup
```

This command will:
1. Install Kamal proxy (Traefik)
2. Create necessary directories
3. Start all accessories
4. Deploy the application

### Regular Deployments

For code updates and routine deployments:

```bash
# Deploy the application
kamal deploy
```

This will:
1. Build the Docker image
2. Push to GitHub Container Registry
3. Pull the image on the server
4. Perform a rolling restart with zero downtime
5. Run health checks

### Build Only

To build and push a new image without deploying:

```bash
# Build and push image
kamal build push
```

### Deploy Specific Version

To deploy a specific image tag:

```bash
# Deploy a specific version
kamal deploy --version=v1.2.3
```

## Managing Accessories

[[memory:4252071]]

### View Logs

```bash
# View Elasticsearch logs
kamal accessory logs elasticsearch

# View PostgreSQL logs
kamal accessory logs postgres

# View Redis logs
kamal accessory logs redis

# Follow logs in real-time
kamal accessory logs elasticsearch --follow
```

### Restart an Accessory

```bash
# Restart Elasticsearch
kamal accessory restart elasticsearch

# Restart PostgreSQL
kamal accessory restart postgres

# Restart Redis
kamal accessory restart redis
```

### Remove and Recreate Accessory

```bash
# Remove an accessory
kamal accessory remove elasticsearch

# Boot an accessory
kamal accessory boot elasticsearch
```

### Reboot All Accessories

```bash
# Reboot all accessories
kamal accessory reboot -a
```

## Application Management

### View Application Logs

```bash
# View recent logs
kamal app logs

# Follow logs in real-time
kamal app logs --follow

# View last 100 lines
kamal app logs --lines 100
```

### Execute Commands in Container

```bash
# Open a shell in the running container
kamal app exec -i bash

# Run a one-off command
kamal app exec "cd /app/backend && python scripts/run_migrations.py"

# Run database migrations
kamal app exec "cd /app/backend && python scripts/run_migrations.py"
```

### Restart Application

```bash
# Restart the application (zero-downtime)
kamal app restart
```

### Stop Application

```bash
# Stop the application
kamal app stop
```

### Start Application

```bash
# Start the application
kamal app start
```

## Server Management

### SSH into Server

```bash
# SSH to the server
kamal app exec -i bash

# Or use direct SSH
ssh ewlarson@ogm.geo4lib.app
```

### View Server Details

```bash
# Show server details
kamal details
```

### View Running Containers

```bash
# List all containers
kamal app containers
```

## Database Operations

### Running Migrations

After deploying new code that includes database migrations:

```bash
# Execute migrations in the container
kamal app exec "cd /app/backend && python scripts/run_migrations.py"
```

### Backup Database

SSH into the server and run:

```bash
# SSH to server
ssh ewlarson@ogm.geo4lib.app

# Create backup
docker exec ogm-api-postgres pg_dump -U ogm_api_user opengeometadata_api > backup_$(date +%Y%m%d).sql

# Compress backup
gzip backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Copy backup to server
scp backup.sql.gz ewlarson@ogm.geo4lib.app:~/

# SSH to server
ssh ewlarson@ogm.geo4lib.app

# Decompress
gunzip backup.sql.gz

# Restore
cat backup.sql | docker exec -i ogm-api-postgres psql -U ogm_api_user opengeometadata_api
```

## Elasticsearch Operations

### Rebuild Index

```bash
# Execute index rebuild in the container
kamal app exec "cd /app/backend && python scripts/run_index.py"
```

### Check Index Health

```bash
# SSH to server and check Elasticsearch
ssh ewlarson@ogm.geo4lib.app
curl -X GET "localhost:9200/_cat/indices?v"
curl -X GET "localhost:9200/opengeometadata_api/_search?size=1&pretty"
```

## Rollback

If a deployment causes issues, you can quickly rollback:

```bash
# Rollback to previous version
kamal rollback [VERSION]
```

To find available versions:

```bash
# List recent deployments
kamal app images
```

## Monitoring & Debugging

### Health Check

The application health check is configured to use `/api/docs`:

```bash
# Check health status
curl https://ogm.geo4lib.app/api/docs
```

### Debug Deployment Issues

```bash
# Check deployment status
kamal details

# View application logs
kamal app logs --lines 200

# Check container status
kamal app containers

# Verify environment variables
kamal app exec "env | grep -i elasticsearch"
```

### Common Issues

**Issue: Container won't start**
```bash
# Check logs for errors
kamal app logs --lines 100

# Verify image was built correctly
kamal app images

# Check server resources
ssh ewlarson@ogm.geo4lib.app "docker ps -a"
```

**Issue: Database connection failures**
```bash
# Verify PostgreSQL is running
kamal accessory logs postgres

# Check database accessibility
kamal app exec "nc -zv ogm-api-postgres 5432"
```

**Issue: Elasticsearch not responding**
```bash
# Check Elasticsearch logs
kamal accessory logs elasticsearch

# Verify Elasticsearch is healthy
ssh ewlarson@ogm.geo4lib.app "curl localhost:9200/_cluster/health?pretty"
```

## Complete Deployment Workflow

Here's a typical workflow for deploying changes:

```bash
# 1. Ensure secrets are set
export KAMAL_REGISTRY_PASSWORD="your_token"
export OPENAI_API_KEY="your_key"

# 2. Verify configuration
kamal config

# 3. Deploy the application
kamal deploy

# 4. Monitor deployment
kamal app logs --follow

# 5. Verify deployment
curl https://ogm.geo4lib.app/api/docs

# 6. If needed, run migrations
kamal app exec "cd /app/backend && python scripts/run_migrations.py"

# 7. If needed, rebuild search index
kamal app exec "cd /app/backend && python scripts/run_index.py"
```

## CI/CD Integration

For automated deployments via GitHub Actions or similar:

```yaml
# Example GitHub Action step
- name: Deploy with Kamal
  env:
    KAMAL_REGISTRY_PASSWORD: ${{ secrets.GITHUB_TOKEN }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    gem install kamal
    kamal deploy
```

## Security Considerations

1. **Never commit secrets**: Keep `.kamal/secrets` safe but never commit actual credentials
2. **SSH key security**: Use strong SSH keys for server access
3. **Registry tokens**: Rotate GHCR tokens regularly
4. **Database passwords**: Use strong passwords for PostgreSQL
5. **Firewall rules**: Ensure only necessary ports are exposed
6. **SSL certificates**: Kamal handles Let's Encrypt automatically
7. **Volume security**: Persistent volumes contain sensitive data

## Volumes & Data Persistence

Kamal manages three persistent volumes:

- `esdata`: Elasticsearch index data
- `pgdata`: PostgreSQL database files
- `redisdata`: Redis cache data

These volumes persist across deployments and container restarts.

### Backing Up Volumes

```bash
# SSH to server
ssh ewlarson@ogm.geo4lib.app

# List volumes
docker volume ls

# Backup a volume
docker run --rm -v pgdata:/data -v $(pwd):/backup \
  alpine tar czf /backup/pgdata_backup.tar.gz /data
```

## Performance Tuning

### Elasticsearch Memory

Adjust heap size in `config/deploy.yml`:

```yaml
ES_JAVA_OPTS: "-Xms4g -Xmx4g"  # Increase to 4GB
```

### Redis Configuration

Modify Redis command for different persistence:

```yaml
cmd: redis-server --appendonly yes --maxmemory 2gb
```

### Application Scaling

Currently configured for single-server deployment. For horizontal scaling, add more servers:

```yaml
servers:
  web:
    hosts:
      - ogm1.geo4lib.app
      - ogm2.geo4lib.app
```

## Troubleshooting

### Container Cleanup

Remove old unused containers:

```bash
kamal prune
```

### Full System Reset

**Warning: This will destroy all data!**

```bash
# Remove everything
kamal remove

# Start fresh
kamal setup
```

## Additional Resources

- [Kamal Documentation](https://kamal-deploy.org/)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Project README](../README.md)

## Support

For deployment issues:
1. Check the application logs: `kamal app logs`
2. Check accessory logs: `kamal accessory logs [name]`
3. Verify server connectivity: `kamal details`
4. Review this documentation
5. Check Kamal documentation: https://kamal-deploy.org/
