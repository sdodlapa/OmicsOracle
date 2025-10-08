# Section 2: Backend API Interface

**Document:** OmicsOracle Web Interfaces Architecture Guide
**Section:** 2 - Backend API Interface
**Date:** June 24, 2025

---

## 🔌 **BACKEND API OVERVIEW**

The Backend API Interface (`web-api-backend/`) provides pure REST API access to OmicsOracle functionality. This interface is designed for developers, applications, and services that need programmatic access to biological data search and analysis capabilities.

### **Key Characteristics**
- **Purpose**: Pure API backend without frontend UI
- **Port**: 8000
- **Technology**: FastAPI + Python
- **Target Users**: Developers, Applications, Services
- **Status**: Production Ready

---

## 🏗️ **ARCHITECTURE**

```
┌─────────────────────────────────────────────────────────┐
│                Backend API Interface                     │
│                    (Port 8000)                          │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────┐ │
│  │   FastAPI App   │  │   API Routes    │  │  Swagger  │ │
│  │                 │  │                 │  │    UI     │ │
│  └─────────────────┘  └─────────────────┘  └───────────┘ │
│            │                    │                        │
│            └────────────────────┼────────────────────────┘
│                                 │
│                     ┌───────────▼───────────┐
│                     │   OmicsOracle Core    │
│                     │      Pipeline         │
│                     └───────────────────────┘
```

### **Core Components**

#### **1. FastAPI Application** (`main.py`)
- High-performance async web framework
- Automatic API documentation generation
- Built-in validation and serialization
- Production-ready ASGI server

#### **2. API Routes**
- `/health` - Health check and status
- `/search` - Biological data search
- `/process-query` - Natural language query processing
- `/api/docs` - Interactive API documentation

#### **3. Data Models**
- Pydantic models for request/response validation
- Type hints for better development experience
- Automatic OpenAPI schema generation

---

## 🚀 **QUICK START**

### **Start the Server**
```bash
cd web-api-backend
./start.sh
```

### **Verify Installation**
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

### **Basic Search**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "breast cancer RNA-seq",
    "max_results": 10,
    "include_sra": false
  }'
```

---

## 📋 **API ENDPOINTS**

### **Health Check**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-24T17:30:00Z",
  "version": "1.0.0",
  "omics_available": true
}
```

### **Search Datasets**
```http
POST /search
Content-Type: application/json
```

**Request:**
```json
{
  "query": "breast cancer",
  "max_results": 10,
  "include_sra": false,
  "organism": "homo sapiens",
  "assay_type": "RNA-seq"
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "GSE123456",
      "title": "Breast cancer RNA-seq analysis",
      "summary": "Comprehensive analysis of...",
      "organism": "Homo sapiens",
      "sample_count": 150,
      "platform": "Illumina HiSeq 4000",
      "publication_date": "2024-01-15",
      "authors": ["Smith J", "Doe A"],
      "pmid": "12345678"
    }
  ],
  "total_count": 1,
  "query": "breast cancer",
  "status": "success",
  "processing_time": 2.34
}
```

### **Process Natural Language Query**
```http
POST /process-query
Content-Type: application/json
```

**Request:**
```json
{
  "query": "Find RNA sequencing data for breast cancer patients treated with chemotherapy",
  "result_format": "json",
  "max_results": 50,
  "include_sra": true
}
```

**Response:**
```json
{
  "query_id": "qry_abc123",
  "original_query": "Find RNA sequencing data...",
  "status": "completed",
  "intent": "dataset_search",
  "entities": {
    "diseases": ["breast cancer"],
    "assay_types": ["RNA-seq"],
    "treatments": ["chemotherapy"]
  },
  "results": [...],
  "ai_summary": "Found 45 relevant datasets...",
  "processing_time": 5.67
}
```

---

## 🔧 **CONFIGURATION**

### **Environment Variables**
```bash
# Server Configuration
OMICS_API_HOST=0.0.0.0
OMICS_API_PORT=8000
OMICS_API_WORKERS=4

# Database Configuration
OMICS_DB_URL=sqlite:///data/omics.db
OMICS_CACHE_URL=redis://localhost:6379

# API Configuration
OMICS_API_KEY_REQUIRED=false
OMICS_RATE_LIMIT=100
OMICS_MAX_RESULTS=1000
```

### **Configuration File** (`config/api.yml`)
```yaml
api:
  host: "0.0.0.0"
  port: 8000
  debug: false
  workers: 4

search:
  default_max_results: 100
  absolute_max_results: 1000
  timeout_seconds: 30

cache:
  enabled: true
  ttl_seconds: 3600
  max_size: 1000
```

---

## 🔗 **INTEGRATION EXAMPLES**

### **Python Client**
```python
import requests
import json

class OmicsOracleClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def search(self, query, max_results=10):
        response = requests.post(
            f"{self.base_url}/search",
            json={
                "query": query,
                "max_results": max_results
            }
        )
        return response.json()

    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage
client = OmicsOracleClient()
results = client.search("breast cancer RNA-seq")
print(f"Found {len(results['results'])} datasets")
```

### **JavaScript/Node.js Client**
```javascript
const axios = require('axios');

class OmicsOracleClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async search(query, maxResults = 10) {
    const response = await axios.post(`${this.baseUrl}/search`, {
      query: query,
      max_results: maxResults
    });
    return response.data;
  }

  async healthCheck() {
    const response = await axios.get(`${this.baseUrl}/health`);
    return response.data;
  }
}

// Usage
const client = new OmicsOracleClient();
client.search('breast cancer RNA-seq')
  .then(results => {
    console.log(`Found ${results.results.length} datasets`);
  });
```

### **R Client**
```r
library(httr)
library(jsonlite)

omics_search <- function(query, max_results = 10, base_url = "http://localhost:8000") {
  url <- paste0(base_url, "/search")

  body <- list(
    query = query,
    max_results = max_results
  )

  response <- POST(
    url,
    body = body,
    encode = "json",
    add_headers("Content-Type" = "application/json")
  )

  content(response, "parsed")
}

# Usage
results <- omics_search("breast cancer RNA-seq")
cat("Found", length(results$results), "datasets\n")
```

---

## 📊 **PERFORMANCE & MONITORING**

### **Performance Metrics**
- **Response Time**: < 2 seconds for typical searches
- **Throughput**: 100+ requests/second
- **Concurrent Users**: 50+ simultaneous connections
- **Memory Usage**: < 2GB under normal load

### **Monitoring Endpoints**
```bash
# Health check with detailed metrics
curl http://localhost:8000/health?detailed=true

# Performance metrics
curl http://localhost:8000/metrics

# Active connections
curl http://localhost:8000/status
```

### **Logging Configuration**
```python
# Custom logging in main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
```

---

## 🔒 **SECURITY & AUTHENTICATION**

### **API Key Authentication** (Optional)
```python
# Enable API key authentication
OMICS_API_KEY_REQUIRED=true
OMICS_API_KEY=your-secret-api-key

# Usage with API key
curl -H "X-API-Key: your-secret-api-key" \
     http://localhost:8000/search
```

### **Rate Limiting**
```python
# Automatic rate limiting per IP
# Default: 100 requests per minute
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/search")
@limiter.limit("10/minute")
async def search_endpoint(request: Request, ...):
    # Search logic
```

### **CORS Configuration**
```python
# Cross-origin resource sharing
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 🛠️ **DEVELOPMENT & TESTING**

### **Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode with hot reload
uvicorn main:app --reload --port 8000

# Run with debugging
python -m debugpy --listen 5678 --wait-for-client -m uvicorn main:app --reload
```

### **Testing**
```bash
# Run API tests
pytest tests/test_api.py -v

# Load testing
ab -n 1000 -c 10 http://localhost:8000/health

# Integration testing
python test_integration.py
```

### **Docker Deployment**
```dockerfile
# Dockerfile for Backend API
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**Next Section: [Legacy UI Interface](./WEB_ARCHITECTURE_SECTION_3_LEGACY_UI.md) →**
