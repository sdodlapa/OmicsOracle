# OmicsOracle Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 50GB+ for data and models
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2

### Software Dependencies

```bash
# Python 3.11+
python --version

# Docker & Docker Compose
docker --version
docker-compose --version

# Redis (for local dev)
redis-cli --version

# Git
git --version
```

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/omicsoracle/api.git
cd api
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

Required environment variables:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/omicsoracle

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# ML Models
ML_MODELS_PATH=./models
EMBEDDING_MODEL=allenai/scibert_scivocab_uncased

# External APIs
PUBMED_API_KEY=your-key-here
SEMANTIC_SCHOLAR_API_KEY=your-key-here

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 4. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Create initial data
python create_sample_datasets.py
```

### 5. Start Redis

```bash
# Linux/macOS
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 6. Run Development Server

```bash
# Standard mode
uvicorn omics_oracle_v2.api.main:app --reload --host 0.0.0.0 --port 8000

# With auto-reload
./start_dev_server.sh
```

Access the API:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health/

## Docker Deployment

### Development with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

Services included:
- API server (port 8000)
- Redis (port 6379)
- PostgreSQL (port 5432)

### Production with Docker Compose

```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl http://localhost:8000/health/ready
```

Services included:
- API server with health checks
- Redis with persistence
- Prometheus (port 9090)
- Grafana (port 3000)

### Custom Docker Build

```bash
# Build image
docker build -f Dockerfile.production -t omicsoracle/api:v1.0.0 .

# Run container
docker run -d \
  --name omicsoracle-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_HOST=redis \
  --restart unless-stopped \
  omicsoracle/api:v1.0.0

# View logs
docker logs -f omicsoracle-api
```

## Production Deployment

### 1. Server Setup (Ubuntu 20.04+)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx (reverse proxy)
sudo apt install nginx -y
```

### 2. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/omicsoracle
```

```nginx
upstream omicsoracle_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.omicsoracle.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.omicsoracle.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/api.omicsoracle.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.omicsoracle.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://omicsoracle_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check (no auth required)
    location /health/ {
        proxy_pass http://omicsoracle_api;
        access_log off;
    }

    # Metrics (restrict access)
    location /metrics {
        deny all;
        return 403;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/omicsoracle /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d api.omicsoracle.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 4. Deploy Application

```bash
# Create application directory
sudo mkdir -p /opt/omics-oracle
cd /opt/omics-oracle

# Clone repository
git clone https://github.com/omicsoracle/api.git .

# Set up environment
sudo nano .env.production

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 5. Database Migration

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec api \
  alembic upgrade head

# Verify
docker-compose -f docker-compose.prod.yml exec api \
  python -c "from omics_oracle_v2.lib.db import get_db; print('DB OK')"
```

### 6. Systemd Service (Alternative)

```bash
sudo nano /etc/systemd/system/omicsoracle.service
```

```ini
[Unit]
Description=OmicsOracle API
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/omics-oracle
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable service:

```bash
sudo systemctl enable omicsoracle
sudo systemctl start omicsoracle
sudo systemctl status omicsoracle
```

## Monitoring

### Prometheus Metrics

Access metrics:
```bash
curl http://localhost:9090/metrics
```

Key metrics:
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request latency
- `redis_cache_hits_total`: Cache hit rate
- `ml_predictions_total`: ML prediction count

### Grafana Dashboards

1. Access Grafana: http://localhost:3000
2. Login: admin/admin (change on first login)
3. Add Prometheus datasource:
   - URL: http://prometheus:9090
   - Save & Test
4. Import dashboard: Upload `config/grafana/dashboards/omicsoracle.json`

### Health Checks

```bash
# Basic health
curl -H "X-API-Key: your-key" http://localhost:8000/health/

# Detailed health
curl -H "X-API-Key: your-key" http://localhost:8000/health/detailed

# Readiness (K8s)
curl http://localhost:8000/health/ready

# Liveness (K8s)
curl http://localhost:8000/health/live
```

### Logging

View logs:

```bash
# API logs
docker-compose -f docker-compose.prod.yml logs -f api

# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific time range
docker-compose -f docker-compose.prod.yml logs --since 1h api

# Save logs
docker-compose -f docker-compose.prod.yml logs --no-color > logs.txt
```

Log format (JSON):

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "omics_oracle_v2.api",
  "message": "Request processed",
  "request_id": "abc-123",
  "duration_ms": 45.2
}
```

## Troubleshooting

### Issue: API Not Starting

```bash
# Check logs
docker-compose logs api

# Common causes:
# 1. Port already in use
sudo lsof -i :8000

# 2. Missing environment variables
docker-compose config

# 3. Database connection
docker-compose exec api python -c "from omics_oracle_v2.lib.db import test_connection; test_connection()"
```

### Issue: Redis Connection Failed

```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Test from API
docker-compose exec api python -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"

# Check network
docker-compose exec api ping redis
```

### Issue: Out of Memory

```bash
# Check memory usage
docker stats

# Increase container memory
# Edit docker-compose.prod.yml:
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
```

### Issue: Slow Responses

```bash
# Check cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace

# Check database connections
docker-compose exec api python -c "from omics_oracle_v2.lib.db import check_pool; check_pool()"

# Profile request
curl -w "@curl-format.txt" -H "X-API-Key: key" http://localhost:8000/api/search?query=test
```

### Issue: SSL Certificate Errors

```bash
# Renew certificate
sudo certbot renew

# Check expiration
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

## Backup & Recovery

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U omicsoracle omicsoracle > backup.sql

# Restore
cat backup.sql | docker-compose exec -T postgres psql -U omicsoracle omicsoracle
```

### Redis Backup

```bash
# Trigger save
docker-compose exec redis redis-cli SAVE

# Copy RDB file
docker cp omicsoracle_redis_1:/data/dump.rdb ./redis-backup.rdb

# Restore
docker cp redis-backup.rdb omicsoracle_redis_1:/data/dump.rdb
docker-compose restart redis
```

## Updates & Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose -f docker-compose.prod.yml build

# Apply migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Rolling restart
docker-compose -f docker-compose.prod.yml up -d --no-deps api
```

### Zero-Downtime Deployment

```bash
# Scale up
docker-compose -f docker-compose.prod.yml up -d --scale api=2

# Update one instance
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api=2 api

# Scale down
docker-compose -f docker-compose.prod.yml up -d --scale api=1
```

## Security Checklist

- [ ] Change default passwords
- [ ] Enable SSL/TLS
- [ ] Configure firewall (ufw/iptables)
- [ ] Set up API key rotation
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Backup encryption keys
- [ ] Implement CORS policies
- [ ] Use secrets management (Vault, AWS Secrets Manager)

## Support

- Documentation: https://docs.omicsoracle.com
- Issues: https://github.com/omicsoracle/api/issues
- Email: support@omicsoracle.com
