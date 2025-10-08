# OmicsOracle Web Interfaces - Detailed Comparison & Usage Guide

## 🔍 **Key Answer: NO CONFLICTS - Completely Separated**

The three web interfaces are **completely independent** and run on different ports. You can use any combination:

- **Original Interface (8001)**: Fully standalone
- **Modern Interface (5173)**: Requires Backend API (8000)
- **Backend API (8000)**: Serves other interfaces + direct API access

---

## 📊 **Detailed Comparison Table**

| Aspect | Original Interface | Modern Interface | Backend API |
|--------|-------------------|------------------|-------------|
| **Port** | 8001 | 5173 | 8000 |
| **Technology** | FastAPI + Static HTML | React + Vite + TypeScript | FastAPI only |
| **Dependencies** | Self-contained | Requires Backend API | Standalone |
| **Startup Time** | ~3 seconds | ~10 seconds | ~5 seconds |
| **Resource Usage** | Low | Medium | Low |
| **User Interface** | Basic HTML forms | Modern React components | None (API only) |
| **Search Features** | Basic search | Advanced search + filters | API endpoints |
| **Data Visualization** | Simple tables | Charts & graphs | Raw JSON |
| **Real-time Updates** | WebSocket | React state + WebSocket | WebSocket |
| **Mobile Support** | Basic responsive | Fully responsive | N/A |
| **Offline Capability** | No | No | N/A |
| **Build Process** | None | npm build required | None |
| **Customization** | Edit HTML/CSS directly | React components | API configuration |

---

## 🎯 **When to Use Each Interface**

### 🧬 **Original Interface (Port 8001)**
**Best for:**
- ✅ Quick testing and demos
- ✅ Legacy system integration
- ✅ Minimal resource environments
- ✅ Educational purposes
- ✅ When you want simplicity
- ✅ No build process needed

**Not ideal for:**
- ❌ Production use with many users
- ❌ Complex data analysis
- ❌ Mobile-first applications

### 🎨 **Modern Interface (Port 5173)**
**Best for:**
- ✅ Daily research and analysis
- ✅ Production environments
- ✅ Multiple users
- ✅ Advanced data visualization
- ✅ Mobile/tablet access
- ✅ Complex search workflows

**Not ideal for:**
- ❌ Simple one-off queries
- ❌ Resource-constrained environments
- ❌ When you need quick setup

### 🔧 **Backend API (Port 8000)**
**Best for:**
- ✅ Custom integrations
- ✅ Third-party applications
- ✅ Programmatic access
- ✅ Batch processing
- ✅ CI/CD pipelines
- ✅ Research automation

**Not ideal for:**
- ❌ Manual/interactive use
- ❌ Non-technical users

---

## 🚀 **Step-by-Step Usage Guide**

### **Setup 1: Original Interface Only (Simplest)**
```bash
# Single command startup
cd web-interface-original
./activate_and_run.sh

# Access: http://localhost:8001
# ✅ Fully functional immediately
# ✅ No other services needed
```

### **Setup 2: Modern Interface with Backend**
```bash
# Terminal 1: Start Backend API
source .venv/bin/activate
python -m uvicorn src.omics_oracle.web.main:app --port 8000

# Terminal 2: Start Modern Interface
cd web-interface
npm install  # First time only
npm run dev

# Access: http://localhost:5173
# ✅ Full modern functionality
# ✅ Advanced features available
```

### **Setup 3: All Three Interfaces (Maximum Flexibility)**
```bash
# Terminal 1: Backend API
source .venv/bin/activate
python -m uvicorn src.omics_oracle.web.main:app --port 8000

# Terminal 2: Original Interface
cd web-interface-original
./activate_and_run.sh

# Terminal 3: Modern Interface
cd web-interface
npm run dev

# Access all three:
# - http://localhost:8000/docs (API documentation)
# - http://localhost:8001 (Original interface)
# - http://localhost:5173 (Modern interface)
```

---

## 🔄 **Data Flow & Architecture**

### **Original Interface (Self-Contained)**
```
User → http://localhost:8001 → Built-in FastAPI → OmicsOracle Pipeline → Results
```

### **Modern Interface (Two-Tier)**
```
User → http://localhost:5173 → React Frontend → http://localhost:8000 → FastAPI Backend → OmicsOracle Pipeline → Results
```

### **Direct API Access**
```
Script/App → http://localhost:8000/api/search → FastAPI Backend → OmicsOracle Pipeline → JSON Results
```

---

## ⚙️ **Configuration & Customization**

### **Original Interface**
- **Config file**: `web-interface-original/main.py`
- **HTML/CSS**: `web-interface-original/index.html`
- **Port**: Change in `main.py` line 364

### **Modern Interface**
- **Config file**: `web-interface/vite.config.ts`
- **Components**: `web-interface/src/components/`
- **API URL**: `web-interface/src/services/api.ts`

### **Backend API**
- **Config file**: `src/omics_oracle/web/main.py`
- **Routes**: `src/omics_oracle/web/routes.py`
- **Models**: `src/omics_oracle/web/models.py`

---

## 🧪 **Testing Each Interface**

### **Health Checks**
```bash
# Original Interface
curl http://localhost:8001/health

# Modern Interface (check if running)
curl http://localhost:5173

# Backend API
curl http://localhost:8000/health
```

### **Search Tests**
```bash
# Original Interface
curl -X POST http://localhost:8001/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "cancer", "max_results": 5}'

# Backend API
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "cancer", "max_results": 5}'

# Modern Interface (use browser)
# Go to http://localhost:5173 and use the search box
```

---

## 💡 **Pro Tips**

### **For Development**
1. **Start with Original Interface** for quick testing
2. **Use Backend API** for automated testing
3. **Use Modern Interface** for user acceptance testing

### **For Production**
1. **Use Modern Interface** for end users
2. **Use Backend API** for integrations
3. **Keep Original Interface** as backup

### **For Troubleshooting**
1. **Check ports**: `lsof -i :8000 -i :8001 -i :5173`
2. **Test individually**: Start one interface at a time
3. **Check logs**: Each interface has its own log output

---

## 🔧 **Quick Troubleshooting**

| Problem | Solution |
|---------|----------|
| Port already in use | `kill -9 $(lsof -t -i:8001)` |
| ModuleNotFoundError | `source .venv/bin/activate` |
| Frontend won't start | `cd web-interface && npm install` |
| Backend connection failed | Check if Backend API is running on 8000 |
| Original interface not found | `cd web-interface-original && ./activate_and_run.sh` |

---

**Summary**: The three interfaces are completely independent, each serving different use cases. Use the Original Interface for simplicity, Modern Interface for full features, and Backend API for integrations. No conflicts exist between them!
