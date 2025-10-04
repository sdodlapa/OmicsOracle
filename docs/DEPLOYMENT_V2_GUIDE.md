# OmicsOracle v2 Deployment Guide

**Version:** 2.0 (Phase 3 Complete)
**Date:** October 4, 2025
**Status:** Production Ready

---

## 🎯 Overview

This guide covers deployment of the OmicsOracle v2 Agent API, featuring:
- 🤖 Agent-based architecture
- 🔄 Workflow orchestration
- 📦 Batch processing
- ⚡ WebSocket real-time updates
- 📊 Prometheus monitoring
- 🎨 Web dashboard

---

## 🏗️ Deployment Options

### 1. Local Development
Quick setup for local development and testing.

### 2. Docker (Recommended)
Containerized deployment with Docker Compose.

### 3. Production Deployment
Scalable production deployment with monitoring.

### 4. Cloud Deployment
Cloud-native deployment (AWS, GCP, Azure).

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Git
- 4GB RAM minimum
- 10GB disk space

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/OmicsOracle.git
cd OmicsOracle

# Checkout Phase 3 branch
git checkout phase-3-agent-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install monitoring dependencies
pip install prometheus-client

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Environment Configuration

Create `.env` file:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE="OmicsOracle Agent API"
API_VERSION="2.0.0"

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","http://localhost:8001"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET","POST","PUT","DELETE","OPTIONS"]
CORS_ALLOW_HEADERS=["*"]

# Agent Configuration
NCBI_EMAIL=your.email@example.com
NCBI_API_KEY=your_ncbi_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Feature Flags
ENABLE_BATCH_PROCESSING=true
ENABLE_WEBSOCKET=true
ENABLE_METRICS=true
```

### Start the Server

```bash
# Start with uvicorn (development)
uvicorn omics_oracle_v2.api.main:app --reload --host 0.0.0.0 --port 8000

# Or start with the provided script
python -m omics_oracle_v2.api.main

# Or use gunicorn (production-like)
gunicorn omics_oracle_v2.api.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info
```

### Verify Installation

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"...","version":"2.0.0",...}

# Test API root
curl http://localhost:8000/

# Access interactive docs
open http://localhost:8000/docs

# Access web dashboard
open http://localhost:8000/dashboard

# Check Prometheus metrics
curl http://localhost:8000/metrics
```

---

## 🐳 Docker Deployment (Recommended)

### Single Container

**Dockerfile for API:**
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir prometheus-client

# Copy application code
COPY omics_oracle_v2/ ./omics_oracle_v2/
COPY pyproject.toml setup.py ./

# Install package
RUN pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash omics && \
    chown -R omics:omics /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R omics:omics /app/logs /app/data

# Switch to non-root user
USER omics

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "omics_oracle_v2.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and Run:**
```bash
# Build image
docker build -t omicsoracle-api:v2 -f Dockerfile.api .

# Run container
docker run -d \
  --name omicsoracle-api \
  -p 8000:8000 \
  -e NCBI_EMAIL=your.email@example.com \
  -e NCBI_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  omicsoracle-api:v2

# View logs
docker logs -f omicsoracle-api

# Stop container
docker stop omicsoracle-api
```

### Docker Compose (Multi-service)

**docker-compose.v2.yml:**
```yaml
version: '3.8'

services:
  # OmicsOracle v2 API
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: omicsoracle-api-v2
    ports:
      - "8000:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - NCBI_EMAIL=${NCBI_EMAIL}
      - NCBI_API_KEY=${NCBI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
      - ENABLE_METRICS=true
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
      - prometheus
    restart: unless-stopped
    networks:
      - omics-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Redis cache (for batch job storage)
  redis:
    image: redis:7.2-alpine
    container_name: omicsoracle-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - omics-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Prometheus (metrics collection)
  prometheus:
    image: prom/prometheus:latest
    container_name: omicsoracle-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    restart: unless-stopped
    networks:
      - omics-network

  # Grafana (metrics visualization)
  grafana:
    image: grafana/grafana:latest
    container_name: omicsoracle-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - omics-network

  # Nginx (reverse proxy)
  nginx:
    image: nginx:alpine
    container_name: omicsoracle-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - omics-network

volumes:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  omics-network:
    driver: bridge
```

**Prometheus Configuration (config/prometheus.yml):**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'omicsoracle'
    environment: 'production'

scrape_configs:
  - job_name: 'omicsoracle-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

**Start Services:**
```bash
# Start all services
docker-compose -f docker-compose.v2.yml up -d

# View logs
docker-compose -f docker-compose.v2.yml logs -f api

# Stop all services
docker-compose -f docker-compose.v2.yml down

# Stop and remove volumes
docker-compose -f docker-compose.v2.yml down -v
```

**Access Services:**
- API: http://localhost:8000
- Dashboard: http://localhost:8000/dashboard
- API Docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

---

## 🏭 Production Deployment

### System Requirements

**Minimum:**
- 2 CPU cores
- 4GB RAM
- 20GB disk space
- Ubuntu 22.04+ or similar

**Recommended:**
- 4+ CPU cores
- 8GB+ RAM
- 50GB SSD storage
- Load balancer
- Monitoring system

### Production Setup

#### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install system dependencies
sudo apt install -y \
  nginx \
  redis-server \
  supervisor \
  build-essential \
  curl \
  git

# Create application user
sudo useradd -r -s /bin/false omicsoracle
sudo mkdir -p /opt/omicsoracle
sudo chown omicsoracle:omicsoracle /opt/omicsoracle
```

#### 2. Application Installation

```bash
# Switch to application user
sudo -u omicsoracle -s

# Clone repository
cd /opt/omicsoracle
git clone https://github.com/your-org/OmicsOracle.git app
cd app
git checkout phase-3-agent-api

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e .
pip install -r requirements.txt
pip install gunicorn prometheus-client

# Set up configuration
mkdir -p /opt/omicsoracle/config
cp config/production.yml.example /opt/omicsoracle/config/production.yml
# Edit configuration

# Create data and log directories
mkdir -p /opt/omicsoracle/{data,logs}
```

#### 3. Systemd Service Configuration

**Create `/etc/systemd/system/omicsoracle-api.service`:**
```ini
[Unit]
Description=OmicsOracle v2 API Service
After=network.target redis.service
Wants=redis.service

[Service]
Type=notify
User=omicsoracle
Group=omicsoracle
WorkingDirectory=/opt/omicsoracle/app
Environment="PATH=/opt/omicsoracle/app/venv/bin"
EnvironmentFile=/opt/omicsoracle/config/production.env

ExecStart=/opt/omicsoracle/app/venv/bin/gunicorn \
  omics_oracle_v2.api.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --access-logfile /opt/omicsoracle/logs/access.log \
  --error-logfile /opt/omicsoracle/logs/error.log \
  --log-level info \
  --timeout 300 \
  --graceful-timeout 30

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=omicsoracle-api

[Install]
WantedBy=multi-user.target
```

**Start and Enable Service:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start omicsoracle-api

# Enable on boot
sudo systemctl enable omicsoracle-api

# Check status
sudo systemctl status omicsoracle-api

# View logs
sudo journalctl -u omicsoracle-api -f
```

#### 4. Nginx Configuration

**Create `/etc/nginx/sites-available/omicsoracle`:**
```nginx
# Upstream application server
upstream omicsoracle_api {
    server 127.0.0.1:8000 fail_timeout=0;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=batch_limit:10m rate=5r/s;

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name api.omicsoracle.com;

    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.omicsoracle.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/api.omicsoracle.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.omicsoracle.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Max upload size
    client_max_body_size 10M;

    # Timeouts
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;

    # Root location
    location / {
        proxy_pass http://omicsoracle_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://omicsoracle_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Batch endpoints with stricter rate limiting
    location /api/v1/batch/ {
        limit_req zone=batch_limit burst=10 nodelay;

        proxy_pass http://omicsoracle_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://omicsoracle_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # Health check (no logging, no rate limit)
    location /health {
        proxy_pass http://omicsoracle_api;
        access_log off;
    }

    # Metrics endpoint (restricted access)
    location /metrics {
        # Restrict to local network or monitoring servers
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;

        proxy_pass http://omicsoracle_api;
        access_log off;
    }

    # Static files
    location /static/ {
        alias /opt/omicsoracle/app/omics_oracle_v2/api/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Dashboard
    location /dashboard {
        proxy_pass http://omicsoracle_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable Site:**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/omicsoracle /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

#### 5. SSL/TLS with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.omicsoracle.com

# Test auto-renewal
sudo certbot renew --dry-run

# Auto-renewal is set up by default via systemd timer
sudo systemctl status certbot.timer
```

#### 6. Redis Configuration

**Edit `/etc/redis/redis.conf`:**
```conf
# Bind to localhost only
bind 127.0.0.1

# Set max memory
maxmemory 512mb
maxmemory-policy allkeys-lru

# Enable persistence
save 900 1
save 300 10
save 60 10000

# AOF persistence
appendonly yes
appendfsync everysec
```

**Restart Redis:**
```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### ECS with Fargate

**Task Definition (task-definition.json):**
```json
{
  "family": "omicsoracle-api-v2",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/omicsoracleTaskRole",
  "containerDefinitions": [
    {
      "name": "omicsoracle-api",
      "image": "YOUR_ECR_REPO/omicsoracle-api:v2",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "API_HOST", "value": "0.0.0.0"},
        {"name": "API_PORT", "value": "8000"},
        {"name": "REDIS_URL", "value": "redis://YOUR_ELASTICACHE_ENDPOINT:6379"}
      ],
      "secrets": [
        {"name": "NCBI_API_KEY", "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:ncbi-api-key"},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:openai-api-key"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/omicsoracle-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "api"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

**Deploy to ECS:**
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_REPO
docker build -t omicsoracle-api:v2 -f Dockerfile.api .
docker tag omicsoracle-api:v2 YOUR_ECR_REPO/omicsoracle-api:v2
docker push YOUR_ECR_REPO/omicsoracle-api:v2

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create or update service
aws ecs create-service \
  --cluster omicsoracle-cluster \
  --service-name omicsoracle-api-v2 \
  --task-definition omicsoracle-api-v2 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=omicsoracle-api,containerPort=8000"
```

#### ElastiCache Redis

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id omicsoracle-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxx \
  --cache-subnet-group-name omicsoracle-subnet-group
```

### Google Cloud Platform

#### Cloud Run Deployment

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/omicsoracle-api:v2

# Deploy to Cloud Run
gcloud run deploy omicsoracle-api \
  --image gcr.io/PROJECT_ID/omicsoracle-api:v2 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "API_HOST=0.0.0.0,API_PORT=8080" \
  --set-secrets "NCBI_API_KEY=ncbi-key:latest,OPENAI_API_KEY=openai-key:latest"
```

#### Cloud Memorystore (Redis)

```bash
# Create Redis instance
gcloud redis instances create omicsoracle-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

### Azure Container Instances

```bash
# Create resource group
az group create --name omicsoracle-rg --location eastus

# Create container instance
az container create \
  --resource-group omicsoracle-rg \
  --name omicsoracle-api \
  --image YOUR_REGISTRY/omicsoracle-api:v2 \
  --cpu 1 \
  --memory 2 \
  --dns-name-label omicsoracle-api \
  --ports 8000 \
  --environment-variables API_HOST=0.0.0.0 API_PORT=8000 \
  --secure-environment-variables NCBI_API_KEY=xxx OPENAI_API_KEY=xxx
```

---

## 📊 Monitoring Setup

### Prometheus Configuration

Already covered in Docker Compose section above. For standalone:

**Install Prometheus:**
```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Create config
cat > prometheus.yml <<EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'omicsoracle-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
EOF

# Start Prometheus
./prometheus --config.file=prometheus.yml
```

### Grafana Dashboards

**Sample Dashboard JSON (save as `omicsoracle-dashboard.json`):**
```json
{
  "dashboard": {
    "title": "OmicsOracle v2 API",
    "panels": [
      {
        "title": "HTTP Request Rate",
        "targets": [
          {
            "expr": "rate(omicsoracle_http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Request Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(omicsoracle_http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Active WebSocket Connections",
        "targets": [
          {
            "expr": "omicsoracle_websocket_active_connections"
          }
        ]
      },
      {
        "title": "Batch Jobs",
        "targets": [
          {
            "expr": "rate(omicsoracle_batch_jobs_total[5m])"
          }
        ]
      }
    ]
  }
}
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
- Never commit secrets to Git
- Use environment files or secret managers
- Rotate API keys regularly

### 2. Network Security
```bash
# Configure firewall (UFW)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct API access
sudo ufw enable
```

### 3. API Security
- Implement rate limiting (shown in Nginx config)
- Add API key authentication
- Use HTTPS in production
- Validate all inputs
- Sanitize outputs

### 4. Container Security
```dockerfile
# Use specific version tags
FROM python:3.11.5-slim

# Run as non-root user
USER omics

# Scan for vulnerabilities
# docker scan omicsoracle-api:v2
```

---

## 🔧 Maintenance

### Backup Strategy

**Backup Script (`/opt/omicsoracle/scripts/backup.sh`):**
```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/backups/omicsoracle"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C /opt/omicsoracle config/

# Backup data
tar -czf $BACKUP_DIR/data_$DATE.tar.gz -C /opt/omicsoracle data/

# Backup logs (last 7 days)
find /opt/omicsoracle/logs -name "*.log" -mtime -7 \
  -exec tar -czf $BACKUP_DIR/logs_$DATE.tar.gz {} +

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Cron Job:**
```bash
# Add to crontab
0 2 * * * /opt/omicsoracle/scripts/backup.sh >> /opt/omicsoracle/logs/backup.log 2>&1
```

### Update Process

**Update Script (`/opt/omicsoracle/scripts/update.sh`):**
```bash
#!/bin/bash
set -e

echo "Starting update process..."

# Stop service
sudo systemctl stop omicsoracle-api

# Backup current version
cd /opt/omicsoracle
sudo -u omicsoracle cp -r app app.backup.$(date +%Y%m%d)

# Update code
cd app
sudo -u omicsoracle git pull origin phase-3-agent-api

# Update dependencies
sudo -u omicsoracle venv/bin/pip install --upgrade pip
sudo -u omicsoracle venv/bin/pip install -r requirements.txt

# Start service
sudo systemctl start omicsoracle-api

# Wait for startup
sleep 10

# Health check
if curl -f http://localhost:8000/health; then
    echo "✅ Update successful"
else
    echo "❌ Update failed, rolling back..."
    sudo systemctl stop omicsoracle-api
    sudo -u omicsoracle rm -rf app
    sudo -u omicsoracle mv app.backup.$(date +%Y%m%d) app
    sudo systemctl start omicsoracle-api
    exit 1
fi
```

### Log Rotation

**Create `/etc/logrotate.d/omicsoracle`:**
```
/opt/omicsoracle/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 omicsoracle omicsoracle
    sharedscripts
    postrotate
        systemctl reload omicsoracle-api > /dev/null 2>&1 || true
    endscript
}
```

---

## 🆘 Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check service status
sudo systemctl status omicsoracle-api

# Check logs
sudo journalctl -u omicsoracle-api -n 100 --no-pager

# Check configuration
sudo -u omicsoracle /opt/omicsoracle/app/venv/bin/python -c "from omics_oracle_v2.api.config import APISettings; print(APISettings())"

# Test manually
sudo -u omicsoracle /opt/omicsoracle/app/venv/bin/uvicorn omics_oracle_v2.api.main:app --host 127.0.0.1 --port 8000
```

#### High Memory Usage

```bash
# Check memory
free -h
htop

# Check number of workers
ps aux | grep gunicorn

# Reduce workers in systemd service
# Edit: ExecStart gunicorn ... -w 2 (instead of 4)
```

#### WebSocket Connection Issues

```bash
# Check Nginx WebSocket config
sudo nginx -t

# Test WebSocket directly
wscat -c ws://localhost:8000/ws/workflows/test_id

# Check firewall
sudo ufw status
```

#### Metrics Not Appearing

```bash
# Test metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus targets
# Visit http://localhost:9090/targets

# Verify Prometheus can reach API
telnet localhost 8000
```

---

## 📈 Performance Tuning

### Gunicorn Workers

```bash
# Formula: (2 × CPU cores) + 1
# For 4 cores: -w 9

# For CPU-bound tasks
--worker-class uvicorn.workers.UvicornWorker

# Timeout for long-running workflows
--timeout 300
```

### Nginx Tuning

```nginx
# Worker processes
worker_processes auto;

# Worker connections
events {
    worker_connections 2048;
}

# Keepalive
keepalive_timeout 65;
keepalive_requests 100;

# Buffering
proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;
```

### Redis Tuning

```conf
# Max memory
maxmemory 1gb
maxmemory-policy allkeys-lru

# Lazy freeing
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (111/114 expected)
- [ ] Environment variables configured
- [ ] Secrets stored securely
- [ ] SSL certificates obtained
- [ ] Firewall rules configured
- [ ] Monitoring set up
- [ ] Backup strategy in place

### Deployment
- [ ] Application installed
- [ ] Services configured and enabled
- [ ] Nginx configured and tested
- [ ] Health check passing
- [ ] Metrics collecting
- [ ] Logs rotating

### Post-Deployment
- [ ] Verify all endpoints working
- [ ] Test WebSocket connections
- [ ] Submit test batch job
- [ ] Check Prometheus metrics
- [ ] Verify Grafana dashboards
- [ ] Test backup and restore
- [ ] Document any customizations

---

*For additional deployment support, consult the [API Reference](API_V2_REFERENCE.md) or [GitHub repository](https://github.com/your-org/OmicsOracle).*
