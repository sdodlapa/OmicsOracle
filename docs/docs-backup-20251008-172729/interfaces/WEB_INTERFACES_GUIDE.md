# OmicsOracle Web Interfaces Guide

This document describes all available web interfaces for OmicsOracle and how to use them.

## Available Web Interfaces

### 1. 🎨 Modern React Interface (Current/Main)
- **Location**: `web-interface/`
- **Technology**: React + Vite + TypeScript
- **Port**: 5173
- **Features**:
  - Modern responsive UI
  - Advanced search capabilities
  - Real-time results
  - Data visualization
  - Mobile-friendly design

### 2. 🧬 Original Web Interface (Legacy/Standalone)
- **Location**: `web-interface-original/`
- **Technology**: FastAPI + Static HTML + JavaScript
- **Port**: 8001
- **Features**:
  - Simple HTML interface
  - Basic search functionality
  - Minimal dependencies
  - Standalone operation

### 3. 🔧 Backend API Server
- **Location**: `src/omics_oracle/web/`
- **Technology**: FastAPI
- **Port**: 8000
- **Purpose**: Provides API endpoints for all interfaces

## Quick Start Guide

### Prerequisites
1. Virtual environment must be created: `python3 -m venv .venv`
2. Main backend dependencies installed: `pip install -r requirements.txt`

### Starting All Interfaces

#### Option 1: Use Individual Scripts

**Start Backend API (Required for all interfaces):**
```bash
# From project root
source .venv/bin/activate
python -m uvicorn src.omics_oracle.web.main:app --host 0.0.0.0 --port 8000
```

**Start Modern React Interface:**
```bash
# From project root
cd web-interface
npm install  # First time only
npm run dev
# Access at: http://localhost:5173
```

**Start Original Interface:**
```bash
# From project root
cd web-interface-original
./activate_and_run.sh
# Access at: http://localhost:8001
```

#### Option 2: Use Make Commands (Recommended)
```bash
# Start backend
make run-backend

# Start modern frontend
make run-frontend

# Start original interface
make run-original
```

### Interface Comparison

| Feature | Modern React | Original HTML | Backend API |
|---------|-------------|---------------|-------------|
| User Interface | ✅ Advanced | ✅ Basic | ❌ API Only |
| Search Functionality | ✅ Full | ✅ Basic | ✅ Full |
| Data Visualization | ✅ Charts | ✅ Tables | ❌ Raw Data |
| Mobile Support | ✅ Responsive | ⚠️ Basic | ❌ N/A |
| Real-time Updates | ✅ Yes | ❌ No | ✅ WebSocket |
| Dependencies | High | Low | Medium |
| Standalone | ❌ No | ✅ Yes | ✅ Yes |

### When to Use Each Interface

**Modern React Interface (Recommended for users):**
- Daily usage and research
- Advanced data analysis
- Mobile/tablet access
- Modern web browser experience

**Original Interface (Good for):**
- Legacy systems
- Minimal resource environments
- Simple queries
- Demonstration purposes
- Educational use

**Backend API (For developers):**
- Custom integrations
- Programmatic access
- Testing and debugging
- Third-party applications

### Testing Interfaces

#### Health Checks
```bash
# Backend API
curl http://localhost:8000/health

# Original Interface
curl http://localhost:8001/health

# Modern Interface (check if running)
curl http://localhost:5173
```

#### Search Tests
```bash
# Backend API
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "BRCA1", "max_results": 5}'

# Original Interface API
curl -X GET "http://localhost:8001/search?query=BRCA1&max_results=5"
```

### Troubleshooting

#### Common Issues

**ModuleNotFoundError:**
- Ensure virtual environment is activated: `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**Port Already in Use:**
- Check running processes: `lsof -i :8000` (or :5173, :8001)
- Kill process: `kill -9 <PID>`

**Frontend Build Issues:**
- Clear node modules: `rm -rf web-interface/node_modules`
- Reinstall: `cd web-interface && npm install`

**Backend Connection Issues:**
- Verify backend is running on port 8000
- Check CORS settings in backend configuration
- Ensure API endpoints are properly configured

### Development Notes

#### File Structure
```
OmicsOracle/
├── web-interface/              # Modern React interface
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── web-interface-original/     # Original HTML interface
│   ├── main.py
│   ├── index.html
│   ├── requirements.txt
│   └── activate_and_run.sh
└── src/omics_oracle/web/      # Backend API
    ├── main.py
    ├── routes.py
    └── models.py
```

#### Adding New Interfaces
1. Create new directory: `web-interface-<name>/`
2. Implement interface with unique port
3. Add startup script
4. Update this guide
5. Add to Makefile if needed

### API Endpoints

#### Backend API (Port 8000)
- `GET /health` - Health check
- `POST /api/search` - Search datasets
- `GET /api/datasets` - List datasets
- `WebSocket /ws` - Real-time updates

#### Original Interface (Port 8001)
- `GET /` - Homepage
- `GET /health` - Health check
- `GET /search` - Search (query parameters)
- `GET /static/` - Static files

---

**Last Updated**: June 24, 2025
**Version**: 1.0.0
