# OmicsOracle Deployment Guide

**Version:** 2.0
**Date:** June 25, 2025
**Status:** Production Deployment

---

## 🎯 Overview

This guide covers the complete deployment process for OmicsOracle, from development setup to production deployment. Choose the deployment method that best fits your infrastructure needs.

---

## 🏗️ Deployment Options

### 1. Development Deployment
Quick setup for local development and testing.

### 2. Docker Deployment
Containerized deployment for consistency across environments.

### 3. Production Deployment
Scalable, production-ready deployment with monitoring.

### 4. Cloud Deployment
Cloud-native deployment on AWS, GCP, or Azure.

---

## 🚀 Quick Start (Development)

### Prerequisites
- Python 3.11+
- Git
- 4GB RAM minimum
- 10GB disk space

### Setup Steps

```bash
# Clone repository
git clone https://github.com/your-org/OmicsOracle.git
cd OmicsOracle

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python scripts/init_database.py

# Start development server
uvicorn src.omics_oracle.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Verification
```bash
# Test API
curl http://localhost:8000/health

# Test CLI
python -m src.omics_oracle.cli search "brain cancer" --limit 5
```

---

## 🐳 Docker Deployment

### Single Container (Development)

```dockerfile
# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.omics_oracle.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build image
docker build -t omics-oracle:latest .

# Run container
docker run -p 8000:8000 \
  -e NCBI_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  omics-oracle:latest
```

### Docker Compose (Multi-service)

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/omics_oracle.db
      - NCBI_API_KEY=${NCBI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  redis_data:
```

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

---

## 🏭 Production Deployment

### System Requirements

**Minimum:**
- 2 CPU cores
- 4GB RAM
- 20GB disk space
- Ubuntu 20.04+ or CentOS 8+

**Recommended:**
- 4 CPU cores
- 8GB RAM
- 50GB SSD storage
- Load balancer
- Monitoring system

### Production Setup

#### 1. System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install system dependencies
sudo apt install nginx postgresql redis-server supervisord

# Create application user
sudo useradd -r -s /bin/false omicsoracle
sudo mkdir -p /opt/omicsoracle
sudo chown omicsoracle:omicsoracle /opt/omicsoracle
```

#### 2. Application Deployment
```bash
# Switch to application user
sudo -u omicsoracle -s

# Clone and setup application
cd /opt/omicsoracle
git clone https://github.com/your-org/OmicsOracle.git app
cd app

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Set up configuration
cp config/production.yml.example config/production.yml
# Edit configuration file

# Initialize database
python scripts/init_database.py
```

#### 3. Service Configuration

**Supervisor Configuration** (`/etc/supervisor/conf.d/omicsoracle.conf`):
```ini
[program:omicsoracle]
command=/opt/omicsoracle/app/venv/bin/gunicorn src.omics_oracle.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
directory=/opt/omicsoracle/app
user=omicsoracle
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/omicsoracle/app.log
environment=PYTHONPATH="/opt/omicsoracle/app"
```

**Nginx Configuration** (`/etc/nginx/sites-available/omicsoracle`):
```nginx
upstream omicsoracle {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    location / {
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://omicsoracle;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /health {
        proxy_pass http://omicsoracle;
        access_log off;
    }
}
```

#### 4. Start Services
```bash
# Enable and start services
sudo systemctl enable supervisor nginx redis-server
sudo systemctl start supervisor nginx redis-server

# Enable site
sudo ln -s /etc/nginx/sites-available/omicsoracle /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Start application
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start omicsoracle
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### ECS with Fargate
```yaml
# docker-compose.yml for ECS
version: '3.8'

services:
  app:
    image: your-registry/omics-oracle:latest
    cpu: 512
    memory: 1024
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - NCBI_API_KEY=${NCBI_API_KEY}
    logging:
      driver: awslogs
      options:
        awslogs-group: /ecs/omics-oracle
        awslogs-region: us-east-1
        awslogs-stream-prefix: app
```

#### RDS Database
```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier omics-oracle-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username omicsoracle \
  --master-user-password your-secure-password \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxxxxx
```

#### ElastiCache Redis
```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id omics-oracle-cache \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

### Google Cloud Platform

#### Cloud Run Deployment
```bash
# Build and push to Container Registry
docker build -t gcr.io/your-project/omics-oracle .
docker push gcr.io/your-project/omics-oracle

# Deploy to Cloud Run
gcloud run deploy omics-oracle \
  --image gcr.io/your-project/omics-oracle \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NCBI_API_KEY=your-key
```

### Azure Container Instances
```bash
# Create container group
az container create \
  --resource-group omics-oracle-rg \
  --name omics-oracle \
  --image your-registry/omics-oracle:latest \
  --dns-name-label omics-oracle-unique \
  --ports 8000 \
  --environment-variables NCBI_API_KEY=your-key
```

---

## 📊 Monitoring and Logging

### Application Monitoring

#### Health Checks
```python
# Health check script
#!/usr/bin/env python3

import requests
import sys

def check_health():
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print("✅ Application healthy")
                return 0
            else:
                print("❌ Application unhealthy")
                return 1
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_health())
```

#### Prometheus Metrics
```python
# Add to your FastAPI app
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)

# Custom metrics
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('omics_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('omics_request_duration_seconds', 'Request duration')
```

### Log Management

#### Structured Logging
```python
# logging.py
import structlog
from structlog.stdlib import LoggerFactory

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

#### Log Rotation
```bash
# /etc/logrotate.d/omicsoracle
/var/log/omicsoracle/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    postrotate
        supervisorctl restart omicsoracle
    endscript
}
```

---

## 🔒 Security Configuration

### SSL/TLS Setup
```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Block direct access to application port
sudo ufw deny 8000
```

### Security Headers
```nginx
# Additional Nginx security
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

---

## 🔧 Maintenance

### Backup Strategy
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/omicsoracle"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
sqlite3 /opt/omicsoracle/data/omics_oracle.db ".backup $BACKUP_DIR/database_$DATE.db"

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C /opt/omicsoracle/app config/

# Backup logs (last 7 days)
find /var/log/omicsoracle -name "*.log" -mtime -7 -exec tar -czf $BACKUP_DIR/logs_$DATE.tar.gz {} +

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Update Process
```bash
#!/bin/bash
# update.sh

# Stop application
sudo supervisorctl stop omicsoracle

# Backup current version
cd /opt/omicsoracle
sudo -u omicsoracle cp -r app app.backup.$(date +%Y%m%d)

# Update code
cd app
sudo -u omicsoracle git pull origin main

# Update dependencies
sudo -u omicsoracle venv/bin/pip install -r requirements.txt

# Run migrations
sudo -u omicsoracle venv/bin/python scripts/migrate.py

# Start application
sudo supervisorctl start omicsoracle

# Verify deployment
sleep 10
curl -f http://localhost:8000/health || {
    echo "Deployment failed, rolling back..."
    sudo supervisorctl stop omicsoracle
    sudo -u omicsoracle rm -rf app
    sudo -u omicsoracle mv app.backup.$(date +%Y%m%d) app
    sudo supervisorctl start omicsoracle
    exit 1
}

echo "✅ Deployment successful"
```

---

## 🆘 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
sudo supervisorctl tail omicsoracle

# Check configuration
python -c "from src.omics_oracle.core.config import get_config; print(get_config())"

# Check dependencies
pip check
```

#### Database Connection Issues
```bash
# Test database connection
sqlite3 /opt/omicsoracle/data/omics_oracle.db ".tables"

# Check permissions
ls -la /opt/omicsoracle/data/
```

#### High Memory Usage
```bash
# Monitor memory
htop
free -h

# Check application metrics
curl http://localhost:8000/api/v1/status
```

#### Slow API Responses
```bash
# Check logs for slow queries
grep "slow" /var/log/omicsoracle/app.log

# Monitor database
sqlite3 /opt/omicsoracle/data/omics_oracle.db "PRAGMA optimize;"
```

---

*For additional deployment support, consult our [GitHub Issues](https://github.com/your-org/OmicsOracle/issues) or contact the development team.*
