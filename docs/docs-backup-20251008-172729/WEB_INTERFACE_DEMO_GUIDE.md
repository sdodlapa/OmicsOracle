# 🌐 OmicsOracle Web Interface Demo Guide

**Date:** June 23, 2025
**Status:** ✅ FULLY OPERATIONAL
**Server:** http://127.0.0.1:8000

---

## 🚀 Quick Start Demo

### 1. **Start the Web Server**
```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
uvicorn src.omics_oracle.web.main_simple:app --reload --port 8000
```

### 2. **Access Points**
- **🌐 Main Web Interface:** http://127.0.0.1:8000
- **📚 API Documentation:** http://127.0.0.1:8000/api/docs
- **📖 ReDoc:** http://127.0.0.1:8000/api/redoc
- **❤️ Health Check:** http://127.0.0.1:8000/health

---

## 🎯 Demo Scenarios

### **Scenario 1: Basic Natural Language Search**

#### **Web Interface:**
1. Open http://127.0.0.1:8000 in your browser
2. Enter query: `"breast cancer gene expression"`
3. Set max results: `5`
4. Click **"Search Datasets"**
5. View results with dataset metadata

#### **API Call:**
```bash
curl -X POST "http://127.0.0.1:8000/api/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "breast cancer gene expression",
       "max_results": 5,
       "include_sra": false,
       "output_format": "json"
     }'
```

**Expected Result:**
```json
{
  "query_id": "query_000001",
  "original_query": "breast cancer gene expression",
  "status": "completed",
  "processing_time": 2.1,
  "entities": [
    {"text": "breast cancer", "label": "DISEASE"},
    {"text": "gene expression", "label": "TECHNIQUE"}
  ],
  "metadata": [
    {
      "geo_id": "GSE244361",
      "title": "Loss of RBM45 inhibits breast cancer progression by reducing the SUMOylation of IRF7 to promote IFNB1 transcription",
      "summary": "Loss of RBM45 inhibits breast cancer progression...",
      "organism": "Homo sapiens",
      "platform_count": 1,
      "platforms": ["GPL24676"],
      "sample_count": 3,
      "submission_date": "Oct 20 2023"
    }
  ]
}
```

---

### **Scenario 2: System Health Monitoring**

#### **Check System Status:**
```bash
curl http://127.0.0.1:8000/health
```

#### **Detailed Status:**
```bash
curl http://127.0.0.1:8000/api/status
```

**Expected Response:**
```json
{
  "status": "healthy",
  "configuration_loaded": true,
  "ncbi_email": "sdodl001@odu.edu",
  "pipeline_initialized": true,
  "active_queries": 0
}
```

---

### **Scenario 3: Advanced Query Types**

#### **Complex Biomedical Query:**
```bash
curl -X POST "http://127.0.0.1:8000/api/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "WGBS methylation human brain development",
       "max_results": 10,
       "include_sra": true,
       "output_format": "json"
     }'
```

#### **Disease-Specific Search:**
```bash
curl -X POST "http://127.0.0.1:8000/api/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Alzheimer disease RNA-seq hippocampus",
       "max_results": 8,
       "include_sra": false,
       "output_format": "summary"
     }'
```

---

### **Scenario 4: Batch Processing Demo**

#### **Multiple Queries at Once:**
```bash
curl -X POST "http://127.0.0.1:8000/api/batch" \
     -H "Content-Type: application/json" \
     -d '{
       "queries": [
         "breast cancer microarray",
         "lung cancer RNA-seq",
         "diabetes gene expression"
       ],
       "max_results": 5,
       "output_format": "json"
     }'
```

---

## 🎨 Web Interface Features

### **Main Dashboard**
- **Search Form:** Natural language query input
- **Real-time Status:** System health indicators
- **Results Display:** Beautiful dataset visualization
- **Export Options:** JSON, CSV, TSV formats

### **Interactive Elements**
- **Auto-complete:** Query suggestions
- **Filter Options:** Organism, platform, date range
- **Sort Controls:** By relevance, date, sample count
- **Download Links:** Direct dataset access

### **System Monitoring**
- **Pipeline Status:** Real-time initialization state
- **Query Queue:** Active processing monitor
- **Performance Metrics:** Response time tracking
- **Error Handling:** User-friendly error messages

---

## 🔧 API Endpoint Reference

### **Core Endpoints**

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/health` | GET | System health check | `curl /health` |
| `/api/status` | GET | Detailed system status | `curl /api/status` |
| `/api/search` | POST | Natural language search | See examples above |
| `/api/dataset/{id}` | GET | Get specific dataset info | `curl /api/dataset/GSE123456` |
| `/api/batch` | POST | Batch query processing | See batch example |

### **Request Models**

#### **SearchRequest:**
```json
{
  "query": "string (required)",
  "max_results": "integer (1-100, default: 10)",
  "include_sra": "boolean (default: false)",
  "output_format": "json|csv|tsv|summary (default: json)"
}
```

#### **BatchRequest:**
```json
{
  "queries": ["string array (max 20)"],
  "max_results": "integer (1-100, default: 10)",
  "output_format": "json|csv|tsv|summary (default: json)"
}
```

---

## 🎭 Demo Script for Presentations

### **5-Minute Demo Flow:**

1. **[0-1 min] System Overview**
   - Show main interface at http://127.0.0.1:8000
   - Highlight clean, modern design
   - Point out real-time status indicators

2. **[1-3 min] Natural Language Search**
   - Enter: "breast cancer gene expression"
   - Show results with metadata
   - Explain entity extraction (DISEASE, TECHNIQUE)

3. **[3-4 min] API Documentation**
   - Open http://127.0.0.1:8000/api/docs
   - Show interactive Swagger interface
   - Demonstrate "Try it out" functionality

4. **[4-5 min] Advanced Features**
   - Show batch processing capability
   - Highlight different output formats
   - Mention SRA integration

### **15-Minute Deep Dive:**

1. **[0-2 min] Architecture Overview**
   - Explain FastAPI + Pydantic foundation
   - Show system status endpoint
   - Discuss pipeline initialization

2. **[2-8 min] Search Capabilities**
   - Multiple query examples
   - Entity recognition demo
   - Result formatting options

3. **[8-12 min] Integration Examples**
   - API calls with curl
   - Python requests examples
   - JavaScript fetch examples

4. **[12-15 min] Production Readiness**
   - Error handling demonstration
   - Performance considerations
   - Scaling discussion

---

## 🔍 Troubleshooting

### **Common Issues:**

1. **Server Won't Start:**
   ```bash
   # Check if port is in use
   lsof -i :8000

   # Use different port
   uvicorn src.omics_oracle.web.main_simple:app --port 8001
   ```

2. **Import Errors:**
   ```bash
   # Install in development mode
   pip install -e .
   ```

3. **Slow Responses:**
   - Check NCBI API rate limits
   - Verify internet connection
   - Monitor system resources

### **Debug Mode:**
```bash
# Start with debug logging
uvicorn src.omics_oracle.web.main_simple:app --reload --log-level debug
```

---

## 🎉 Success Indicators

### **✅ System Healthy When:**
- Health endpoint returns `{"status": "healthy"}`
- Pipeline initialization shows `true`
- Search queries return structured results
- Entity extraction identifies biomedical terms
- Response times < 5 seconds

### **🎯 Demo Success Criteria:**
- Natural language queries work
- Results include proper metadata
- API documentation is accessible
- Error handling graceful
- Performance acceptable

---

## 🚀 Next Steps

After successful demo:
1. **Production Deployment:** Docker containerization
2. **Enhanced UI:** React.js frontend
3. **Advanced Features:** Real-time WebSocket updates
4. **Integration:** External API connections
5. **Analytics:** Query performance monitoring

---

**📞 Support:** For issues, check logs in terminal or contact development team
**🔗 Resources:** See `DEVELOPMENT_PLAN.md` for roadmap and `CORE_PHILOSOPHY.md` for principles
