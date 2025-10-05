# OmicsOracle Frontend Testing Guide

## 🎯 Current Status

The OmicsOracle frontend dashboard exists but has **authentication and database configuration issues** that need to be fixed for it to work properly.

## ❌ Issues Found

### 1. **Database Configuration Error**
- **Problem**: App tries to connect to PostgreSQL but PostgreSQL isn't running
- **Error**: `ConnectionRefusedError: [Errno 61] Connection refused`
- **Root Cause**: Config defaults to PostgreSQL, but .env uses SQLite with wrong variable names

### 2. **Authentication Required**
- **Problem**: Dashboard workflow execution returns `401 Unauthorized`
- **Root Cause**: API endpoints require JWT authentication but dashboard doesn't have auth flow

### 3. **Redis Not Required But Causing Warnings**
- **Problem**: Redis warnings on every request
- **Status**: Non-critical - app falls back to memory cache

## ✅ Fixes Applied

### Fix 1: Database Configuration
Updated `.env` to use correct SQLite configuration:

```bash
# Old (incorrect)
DATABASE_URL=sqlite:///data/omics_oracle.db

# New (correct)
OMICS_DB_URL=sqlite+aiosqlite:///./omics_oracle.db
```

### Fix 2: Database Session Error Handling
Enhanced `omics_oracle_v2/database/session.py` to:
- Create SQLite database file and directories automatically
- Better error handling and logging
- Retry logic for initialization

## 🚀 How to Test the Frontend Now

### Step 1: Start the Server

```bash
cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle
source venv/bin/activate
python -m omics_oracle_v2.api.main
```

### Step 2: Access the Dashboard

Open in browser: **http://localhost:8000/dashboard**

### Step 3: Test Without Authentication (Option A - Quick Test)

Create a test user first using the API:

```bash
# Register a test user
curl -X POST "http://localhost:8000/api/v2/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#",
    "username": "testuser",
    "full_name": "Test User"
  }'

# Login to get token
curl -X POST "http://localhost:8000/api/v2/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#"
  }'
```

Copy the `access_token` from the response.

### Step 4: Update Dashboard to Use Token

**Temporary Fix**: Modify the dashboard JavaScript to include the token:

1. Open: http://localhost:8000/dashboard
2. Open browser DevTools (F12)
3. Go to Console tab
4. Paste this code (replace YOUR_TOKEN):

```javascript
// Store token
localStorage.setItem('access_token', 'YOUR_TOKEN_HERE');

// Modify fetch to include token
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    const token = localStorage.getItem('access_token');
    if (token) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    return originalFetch(url, options);
};
```

Now try executing a workflow!

## 🔧 Permanent Fixes Needed

### Option 1: Add Login to Dashboard (Recommended)

Add a login form to `omics_oracle_v2/api/static/dashboard.html`:

```html
<!-- Add before workflow section -->
<div class="card" id="login-card">
    <h2>Login</h2>
    <div class="form-group">
        <label>Email</label>
        <input type="email" id="email" placeholder="test@example.com">
    </div>
    <div class="form-group">
        <label>Password</label>
        <input type="password" id="password">
    </div>
    <button class="btn" onclick="login()">Login</button>
</div>

<script>
async function login() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    const response = await fetch('/api/v2/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });
    
    if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        document.getElementById('login-card').style.display = 'none';
        showMessage('workflow-message', 'Login successful!', 'success');
    } else {
        showMessage('workflow-message', 'Login failed', 'error');
    }
}

// Auto-include token in all requests
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    const token = localStorage.getItem('access_token');
    if (token && !url.includes('/auth/')) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    return originalFetch(url, options);
};
</script>
```

### Option 2: Create Demo/Test Endpoints

Create unauthenticated demo endpoints in `omics_oracle_v2/api/routes/demo.py`:

```python
"""Demo endpoints for testing without authentication."""

from fastapi import APIRouter, Depends
from omics_oracle_v2.agents import Orchestrator
from omics_oracle_v2.api.dependencies import get_orchestrator
from omics_oracle_v2.api.models.workflow import WorkflowRequest, WorkflowResponse

router = APIRouter(tags=["Demo"], prefix="/api/demo")

@router.post("/execute", response_model=WorkflowResponse)
async def demo_execute(
    request: WorkflowRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """Execute workflow without authentication (DEMO ONLY)."""
    # Limited to simple queries for demo
    return await orchestrator.execute(...)
```

## 📊 Testing Checklist

- [x] Database configuration fixed
- [x] SQLite initialization working
- [ ] Authentication flow added to dashboard
- [ ] Test user created
- [ ] Workflow execution working
- [ ] Results display working
- [ ] WebSocket connection working
- [ ] Batch jobs working

## 🧬 Sample Test Queries

Once authentication is working, try these:

```
1. DNA methylation and HiC joint profiling
2. Single-cell RNA sequencing in breast cancer
3. ATAC-seq data for chromatin accessibility
4. Multi-omics integration in diabetes
5. Spatial transcriptomics brain tissue
```

## 🐛 Debugging Tips

### Check Server Logs
```bash
# Watch logs in real-time
tail -f logs/omics_oracle.log
```

### Test API Directly
```bash
# Health check
curl http://localhost:8000/health

# List available endpoints
curl http://localhost:8000/openapi.json | jq '.paths | keys'
```

### Check Database
```bash
# Verify SQLite database was created
ls -lh omics_oracle.db

# Query database
sqlite3 omics_oracle.db "SELECT * FROM users;"
```

## 📝 Next Steps

1. **Immediate**: Implement Option 1 (Add login to dashboard)
2. **Short-term**: Add token refresh logic
3. **Medium-term**: Add user registration to dashboard
4. **Long-term**: Build full React/Vue frontend

## 🎉 Success Criteria

The frontend will be fully working when:
- ✅ Server starts without errors
- ✅ Dashboard loads at /dashboard
- ✅ User can login
- ✅ Workflows execute and return results
- ✅ Results display properly
- ✅ WebSocket updates work
- ✅ Batch jobs can be submitted and tracked

---

**Current Status**: Database fixed ✅ | Auth pending ⏳ | Frontend partially working ⚠️
