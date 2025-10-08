# Section 1: Architecture Overview

**Document:** OmicsOracle Web Interfaces Architecture Guide
**Section:** 1 - Architecture Overview
**Date:** June 24, 2025

---

## 🏗️ **SYSTEM ARCHITECTURE**

OmicsOracle features a **multi-interface architecture** designed for flexibility, scalability, and separation of concerns. Each interface operates independently while sharing the core OmicsOracle pipeline.

```
┌─────────────────────────────────────────────────────────────┐
│                    OmicsOracle Core System                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   NLP Module    │  │ GEO Integration │  │ AI Summarization││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │ Pipeline Engine │  │ Data Processing │  │   Cache Layer   ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
          ┌─────────▼─────────┐ │ ┌─────────▼─────────┐
          │   Shared venv/    │ │ │   Configuration   │
          │   Dependencies    │ │ │     & Data        │
          └───────────────────┘ │ └───────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌─────────▼────────┐    ┌─────────▼────────┐
│  web-api-      │    │   web-ui-        │    │   web-ui-        │
│  backend/      │    │   legacy/        │    │   modern/        │
│  (Port 8000)   │    │   (Port 8001)    │    │   (Port 5173)    │
│                │    │                  │    │                  │
│ Pure REST API  │    │ FastAPI + HTML   │    │ React + TypeScript│
└────────────────┘    └──────────────────┘    └──────────────────┘
                                │
                      ┌─────────▼────────┐
                      │   web-ui-        │
                      │   stable/        │
                      │   (Port 8080)    │
                      │                  │
                      │ FastAPI + HTML   │
                      │ (PRODUCTION)     │
                      └──────────────────┘
```

## 🎯 **DESIGN PRINCIPLES**

### **1. Independence**
- **Separate Ports**: Each interface uses unique ports (8000, 8001, 5173, 8080)
- **Isolated Codebases**: No shared code files between interfaces
- **Independent Startup**: Can run any combination without conflicts

### **2. Shared Foundation**
- **Common Pipeline**: All interfaces use the same OmicsOracle core
- **Shared Dependencies**: Single `venv/` environment for consistency
- **Unified Configuration**: Common config system and data sources

### **3. Purpose-Driven**
- **Backend API**: Pure API for programmatic access
- **Legacy UI**: Fallback interface for compatibility
- **Modern UI**: Future-focused React development
- **Stable UI**: Current production interface for end users

### **4. Scalability**
- **Naming Convention**: `web-{type}-{descriptor}/` allows unlimited interfaces
- **Modular Design**: Easy to add new interfaces without affecting existing ones
- **Technology Flexibility**: Each interface can use different tech stacks

---

## 📁 **DIRECTORY STRUCTURE**

```
OmicsOracle/
├── src/                          # Core OmicsOracle package
│   └── omics_oracle/
│       ├── pipeline/             # Main processing pipeline
│       ├── core/                 # Configuration and utilities
│       ├── nlp/                  # Natural language processing
│       ├── geo_tools/            # GEO database integration
│       └── services/             # Support services
├── venv/                         # Shared virtual environment
├── data/                         # Shared data and cache
├── config/                       # Configuration files
│
├── web-api-backend/              # Backend API Interface
│   ├── main.py                   # API server
│   ├── start.sh                  # Startup script
│   └── README.md                 # API documentation
│
├── web-ui-legacy/                # Legacy UI Interface
│   ├── main.py                   # Legacy server
│   ├── index.html                # Legacy frontend
│   ├── start.sh                  # Startup script
│   └── README.md                 # Legacy documentation
│
├── web-ui-modern/                # Modern React Interface
│   ├── src/                      # React source code
│   ├── package.json              # Node dependencies
│   ├── vite.config.ts            # Vite configuration
│   └── README.md                 # Modern UI documentation
│
└── web-ui-stable/                # Stable UI Interface
    ├── main.py                   # Stable server
    ├── start.sh                  # Startup script
    ├── requirements.txt          # Python dependencies
    └── README.md                 # Stable UI documentation
```

---

## 🔧 **NAMING CONVENTION**

### **Pattern**: `web-{type}-{descriptor}/`

#### **Types**
- **`api`** - Backend APIs without frontend
- **`ui`** - User interfaces with frontend components

#### **Descriptors**
- **`backend`** - Pure API backend services
- **`legacy`** - Older/deprecated interfaces (maintained for compatibility)
- **`modern`** - Latest architecture and technologies
- **`stable`** - Production-ready, actively used interfaces
- **`experimental`** - Development/testing interfaces (future)
- **`mobile`** - Mobile-specific interfaces (future)
- **`admin`** - Administrative interfaces (future)

#### **Future Examples**
```
web-api-backend/          # Current REST API
web-api-graphql/          # Future GraphQL API
web-api-admin/            # Admin-only endpoints

web-ui-stable/            # Current production UI
web-ui-modern/            # Next-generation UI
web-ui-legacy/            # Compatibility fallback
web-ui-mobile/            # Mobile-optimized UI
web-ui-embedded/          # Embeddable widgets
```

---

## 🔄 **INTERFACE LIFECYCLE**

### **Development Stages**
1. **Experimental** → **Modern** → **Stable** → **Legacy**
2. New interfaces start as "experimental" or "modern"
3. Proven interfaces become "stable" (production)
4. Outdated interfaces become "legacy" (compatibility)

### **Current Lifecycle Status**
```
web-ui-legacy/    [Legacy]     ← Maintained for compatibility
web-ui-stable/    [Stable]     ← Current production interface
web-ui-modern/    [Modern]     ← Active development
web-api-backend/  [Backend]    ← Core API service
```

---

## 📊 **INTERFACE COMPARISON**

| Aspect | Backend API | Legacy UI | Modern UI | Stable UI |
|--------|-------------|-----------|-----------|-----------|
| **Purpose** | REST API | Fallback | Future | Production |
| **Technology** | FastAPI | FastAPI+HTML | React+TS | FastAPI+HTML |
| **Target Users** | Developers | Legacy Users | Power Users | All Users |
| **Maintenance** | Active | Minimal | Active | Active |
| **Data Access** | Direct API | Real Pipeline | API + Frontend | Real Pipeline |
| **Performance** | High | Medium | High | High |
| **UI Quality** | N/A | Basic | Modern | Good |

---

## 🚀 **INTEGRATION PATTERNS**

### **Direct Integration** (Backend API)
```python
import requests
response = requests.post("http://localhost:8000/search",
                        json={"query": "breast cancer"})
```

### **Browser Integration** (UI Interfaces)
```html
<!-- Embed search widget -->
<iframe src="http://localhost:8080/search?embedded=true"
        width="800" height="600"></iframe>
```

### **Microservice Pattern**
```yaml
# Docker Compose example
services:
  omics-api:
    build: ./web-api-backend
    ports: ["8000:8000"]

  omics-ui:
    build: ./web-ui-stable
    ports: ["8080:8080"]
    depends_on: [omics-api]
```

---

**Next Section: [Backend API Interface](./WEB_ARCHITECTURE_SECTION_2_BACKEND_API.md) →**
