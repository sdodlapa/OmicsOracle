# 🚀 OmicsOracle Quick Start Guide

## One-Command Startup

```bash
cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle && ./start_dev_server.sh
```

## Quick Test Commands

```bash
# Test health
curl http://localhost:8000/health

# Create test user
curl -X POST "http://localhost:8000/api/v2/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@omics.com","password":"TestPass123!","username":"testuser","full_name":"Test User"}'

# Login (copy the token from response)
curl -X POST "http://localhost:8000/api/v2/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@omics.com","password":"TestPass123!"}'

# Test query (replace YOUR_TOKEN)
curl -X POST "http://localhost:8000/api/v2/agents/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"DNA methylation and HiC profiling"}'
```

## Browser Setup

1. **Open:** http://localhost:8000/dashboard
2. **Press F12** → Console
3. **Paste** (replace token):
```javascript
localStorage.setItem('access_token', 'YOUR_TOKEN_HERE');
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    const token = localStorage.getItem('access_token');
    if (token && !url.includes('/auth/')) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    return originalFetch(url, options);
};
console.log('✅ Ready!');
```
4. **Execute workflow** with your query!

## Test Credentials

- **Email:** test@omics.com
- **Password:** TestPass123!

## URLs

- Dashboard: http://localhost:8000/dashboard
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Sample Queries

```
DNA methylation and HiC joint profiling
Single-cell RNA-seq in breast cancer
ATAC-seq chromatin accessibility data
Multi-omics integration in diabetes
Spatial transcriptomics brain tissue
```

---
**Status:** ✅ Working with authentication
