# OmicsOracle Startup Guide

## 📋 Overview

OmicsOracle has **two main components**:
1. **FastAPI Backend** - REST API server (port 8000)
2. **Streamlit Dashboard** - Web UI (port 8502)

## 🚀 Quick Start

### **Main Startup Script (RECOMMENDED)**
**File:** `start_omics_oracle.sh` (in root directory)

Starts **both** API server and Dashboard together with SSL bypass enabled.

```bash
./start_omics_oracle.sh
```

**Access Points:**
- 📊 **Dashboard:** http://localhost:8502
- 🔌 **API Server:** http://localhost:8000
- 📝 **API Docs:** http://localhost:8000/docs
- ✅ **Health Check:** http://localhost:8000/health

**Features:**
- ✅ Starts both services
- ✅ SSL bypass enabled (works on Georgia Tech VPN)
- ✅ Port availability checks
- ✅ Graceful shutdown on Ctrl+C
- ✅ Process monitoring
- ✅ Log files: `/tmp/omics_api.log` and `/tmp/omics_dashboard.log`

**What SSL bypass does:**
- Sets `PYTHONHTTPSVERIFY=0`
- Clears `SSL_CERT_FILE`
- Allows connections through self-signed certificates

⚠️ **Security Note:** SSL verification is disabled for institutional networks (Georgia Tech, corporate networks). Only use on trusted networks!

---

## � Advanced Options

### **Dashboard Only**
**File:** `scripts/run_dashboard.py`

Starts **only** the Streamlit dashboard.

```bash
python scripts/run_dashboard.py --port 8502
```

**Options:**
- `--config default` - Standard features
- `--config minimal` - Minimal features
- `--config research` - Full research features
- `--port 8502` - Port number (default: 8501)
- `--host localhost` - Host to bind to

**Requires:** API server running on port 8000

---

## 🎯 Recommended Workflow

### For Full Application (API + UI):
```bash
# Start both services (SSL bypass enabled)
./start_omics_oracle.sh
```

### For Dashboard Only:
```bash
# Start just the dashboard (requires API running separately)
python scripts/run_dashboard.py --port 8502
```

### For Testing:
```bash
# Run test server (SQLite, development mode)
./scripts/testing/start_test_server.sh
```

---

## 📊 Component Details

### FastAPI Backend
- **Port:** 8000
- **Framework:** FastAPI (async Python)
- **Database:** SQLite (default) or PostgreSQL
- **Features:**
  - 9 ML-powered endpoints
  - Redis caching (47,418x speedup)
  - Async search across multiple sources
  - Citation prediction
  - Trend analysis
  - Biomarker search

### Streamlit Dashboard
- **Port:** 8502
- **Framework:** Streamlit (Python)
- **Features:**
  - Interactive search interface
  - Visualization tools
  - Analytics dashboard
  - Research trend charts
  - Citation network graphs

---

## 🔍 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
lsof -ti:8000

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Check port 8502
lsof -ti:8502 | xargs kill -9
```

### Logs Location
```bash
# API logs
tail -f /tmp/omics_api.log

# Dashboard logs
tail -f /tmp/omics_dashboard.log
```

### Virtual Environment Issues
```bash
# Ensure venv is activated
source venv/bin/activate

# Verify Python environment
which python  # Should show: .../OmicsOracle/venv/bin/python
```

### SSL Certificate Issues (Georgia Tech)
Use the SSL bypass script:
```bash
./scripts/archive/start_omics_oracle_ssl_bypass.sh
```

---

## 🧪 Testing

### Quick Health Check
```bash
# API health
curl http://localhost:8000/health

# Search test
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "CRISPR", "max_results": 5}'
```

### End-to-End Test
```bash
# Run comprehensive test suite
python examples/test_end_to_end.py
```

---

## 📝 Environment Variables

### Required for Full Functionality
Create a `.env` file:
```bash
# NCBI (PubMed) Access
NCBI_EMAIL=your.email@gatech.edu
NCBI_API_KEY=your_api_key

# OpenAI (for ML features)
OPENAI_API_KEY=your_openai_key

# Database (optional, defaults to SQLite)
OMICS_DB_URL=sqlite+aiosqlite:///./omics_oracle.db

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379
```

---

## 🎓 Summary

| What You Want | Script to Use | Ports |
|---------------|---------------|-------|
| **Full app (API + UI)** | `./start_omics_oracle.sh` | 8000, 8502 |
| **Dashboard only** | `python scripts/run_dashboard.py` | 8502 |
| **Testing** | `./scripts/testing/start_test_server.sh` | 8000 |

**Most Common Usage:**
```bash
./start_omics_oracle.sh
```
*(Starts both API + Dashboard with SSL bypass for institutional networks)*
