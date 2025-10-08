# 🏗️ OmicsOracle Web Interfaces Architecture Guide

**Document Version:** 2.0
**Date:** June 24, 2025
**Status:** ACTIVE - Post-Reorganization
**Owner:** OmicsOracle Development Team

---

## 📋 **DOCUMENT OVERVIEW**

This comprehensive guide documents the complete web interface architecture of OmicsOracle after the major reorganization. The system now features **4 distinct, independent web interfaces** each serving specific purposes and user needs.

## 🎯 **KEY IMPROVEMENTS**

✅ **Clear Naming Convention**: All interfaces follow `web-{type}-{descriptor}/` pattern
✅ **Complete Independence**: No interference between interfaces
✅ **Scalable Architecture**: Ready for future interface additions
✅ **Production Ready**: Stable interface with real OmicsOracle integration

---

## 📚 **DOCUMENT SECTIONS**

This guide is divided into detailed sections for maintainability and clarity:

### **Section 1: Architecture Overview**
- [Architecture Overview](./WEB_ARCHITECTURE_SECTION_1_OVERVIEW.md)
- System architecture, naming conventions, and design principles

### **Section 2: Backend API Interface**
- [Backend API Details](./WEB_ARCHITECTURE_SECTION_2_BACKEND_API.md)
- Pure REST API for programmatic access (Port 8000)

### **Section 3: Legacy UI Interface**
- [Legacy UI Details](./WEB_ARCHITECTURE_SECTION_3_LEGACY_UI.md)
- Original full-stack interface (Port 8001)

### **Section 4: Modern React Interface**
- [Modern UI Details](./WEB_ARCHITECTURE_SECTION_4_MODERN_UI.md)
- Next-generation React frontend (Port 5173)

### **Section 5: Stable UI Interface**
- [Stable UI Details](./WEB_ARCHITECTURE_SECTION_5_STABLE_UI.md)
- Current production-ready interface (Port 8080)

### **Section 6: Development & Operations**
- [DevOps Guide](./WEB_ARCHITECTURE_SECTION_6_DEVOPS.md)
- Testing, monitoring, deployment, and maintenance

### **Section 7: Usage Examples**
- [Usage Examples](./WEB_ARCHITECTURE_SECTION_7_EXAMPLES.md)
- Practical examples and integration patterns

---

## 🚀 **QUICK START**

### **For Users**
```bash
# Start the stable interface (recommended)
cd web-ui-stable && ./start.sh
# Access: http://localhost:8080
```

### **For Developers**
```bash
# Start backend API
cd web-api-backend && ./start.sh
# Access: http://localhost:8000/docs

# Start modern React interface
cd web-ui-modern && npm run dev
# Access: http://localhost:5173
```

### **For API Integration**
```bash
# Health check
curl http://localhost:8000/health

# Search example
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "breast cancer", "max_results": 5}'
```

---

## 🎯 **CURRENT STATUS**

| Interface | Status | Port | Purpose | Ready For |
|-----------|--------|------|---------|-----------|
| **Backend API** | ✅ Ready | 8000 | REST API | Production |
| **Legacy UI** | ⚠️ Legacy | 8001 | Fallback | Maintenance |
| **Modern UI** | 🚧 Development | 5173 | Future | Development |
| **Stable UI** | ✅ **Active** | 8080 | **Current** | **Users** |

---

## 🛠️ **MAINTENANCE STATUS**

- **Last Updated**: June 24, 2025
- **Next Review**: July 2025
- **Breaking Changes**: None planned
- **Compatibility**: All interfaces maintained

---

**Continue to Section 1: [Architecture Overview](./WEB_ARCHITECTURE_SECTION_1_OVERVIEW.md) →**
