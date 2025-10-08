# OmicsOracle System Architecture

**Version:** 2.0
**Date:** June 25, 2025
**Status:** Production Architecture

---

## 🏗️ Architecture Overview

OmicsOracle follows a modular, layered architecture designed for scalability, maintainability, and scientific rigor. The system is built with microservices principles while maintaining simplicity for research workflows.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                          │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   CLI Interface │   Web Interface │   API Interface │  Mobile   │
│   (Click-based) │   (React/Flask) │   (FastAPI)     │  (Future) │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                           │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   Query Router  │   Auth Manager  │   Rate Limiter  │  Monitor  │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                              │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   GEO Service   │   NLP Service   │  Cache Service  │  AI Agent │
│                 │                 │                 │  Service  │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   GEO Database  │   Cache Store   │   Config Store  │  Logs     │
│   (External)    │   (SQLite/File) │   (YAML/JSON)   │  (Files)  │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
```

---

## 📦 System Components

### 1. Core Layer

```
src/omics_oracle/core/
├── __init__.py
├── config.py          # Configuration management
├── exceptions.py      # Custom exception classes
├── logging.py         # Logging infrastructure
└── models.py          # Data models and schemas
```

**Responsibilities:**
- Configuration management across environments
- Centralized exception handling
- Structured logging and monitoring
- Core data models and validation

### 2. GEO Tools Layer

```
src/omics_oracle/geo_tools/
├── __init__.py
├── ncbi_client.py     # NCBI API client
├── geo_parser.py      # GEO data parsing
├── metadata_extractor.py  # Metadata extraction
└── validators.py      # GEO-specific validation
```

**Responsibilities:**
- NCBI API integration with rate limiting
- GEO dataset parsing and normalization
- Metadata extraction and standardization
- Data quality validation

### 3. NLP Processing Layer

```
src/omics_oracle/nlp/
├── __init__.py
├── preprocessor.py    # Text preprocessing
├── summarizer.py      # AI summarization
├── classifier.py      # Content classification
└── entity_extractor.py  # Scientific entity extraction
```

**Responsibilities:**
- Natural language query processing
- AI-powered dataset summarization
- Scientific entity recognition
- Content classification and tagging

### 4. API Layer

```
src/omics_oracle/api/
├── __init__.py
├── main.py           # FastAPI application
└── endpoints/        # API endpoint definitions
```

**Responsibilities:**
- RESTful API endpoints
- Request/response validation
- Authentication and authorization
- API documentation (OpenAPI/Swagger)

### 5. CLI Layer

```
src/omics_oracle/cli/
├── __init__.py
├── main.py           # CLI entry point
├── commands/         # Command implementations
└── utils.py          # CLI utilities
```

**Responsibilities:**
- Command-line interface
- Interactive query processing
- Batch operations
- Configuration management

### 6. Web Interface Layer

```
src/omics_oracle/web/
├── __init__.py
├── app.py            # Web application
├── routes/           # Web routes
├── templates/        # HTML templates
└── static/           # CSS/JS assets
```

**Responsibilities:**
- Web-based user interface
- Interactive search and visualization
- Real-time query processing
- Export and sharing capabilities

---

## 🔄 Data Flow Architecture

### Query Processing Pipeline

```
1. User Input
   ├── CLI: Natural language query
   ├── Web: Form-based or natural language
   └── API: JSON-formatted query

2. Query Preprocessing
   ├── Input validation and sanitization
   ├── Natural language parsing
   ├── Query intent classification
   └── Parameter extraction

3. Data Retrieval
   ├── Cache lookup for existing results
   ├── GEO database query construction
   ├── NCBI API requests with rate limiting
   └── Response validation and parsing

4. Data Processing
   ├── Metadata extraction and normalization
   ├── Scientific entity recognition
   ├── Content classification
   └── Quality assessment

5. AI Enhancement
   ├── Context-aware summarization
   ├── Related dataset suggestions
   ├── Research trend analysis
   └── Citation and reference extraction

6. Response Generation
   ├── Format-specific output generation
   ├── Caching of processed results
   ├── Response validation
   └── Delivery to user interface
```

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Level Caching                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│   L1: Memory    │   L2: SQLite    │   L3: File System      │
│   - Query cache │   - Summaries   │   - Raw GEO data       │
│   - Session     │   - Metadata    │   - Export files       │
│   - User prefs  │   - Analytics   │   - Logs & metrics     │
└─────────────────┴─────────────────┴─────────────────────────┘
```

**Cache Invalidation:**
- Time-based expiration (24h for GEO data, 1h for summaries)
- Version-based invalidation for configuration changes
- Manual cache clearing for development and testing
- Intelligent cache warming for popular queries

---

## 🔧 Configuration Management

### Environment-Based Configuration

```yaml
# config/base.yml - Base configuration
app:
  name: "OmicsOracle"
  version: "2.0.0"
  debug: false

# config/development.yml - Development overrides
app:
  debug: true
  log_level: "DEBUG"

ncbi:
  rate_limit: 1  # Slower for development
  timeout: 30

# config/production.yml - Production overrides
app:
  log_level: "INFO"

ncbi:
  rate_limit: 3  # NCBI recommended limit
  timeout: 10

logging:
  level: "INFO"
  format: "json"
  handlers:
    - file
    - syslog
```

---

## 🛡️ Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Input Val.    │   Rate Limiting │   Access Control       │
│   - Schema val. │   - Per IP      │   - Role-based         │
│   - Sanitization│   - Per user    │   - Resource-level     │
│   - Type safety │   - Per endpoint│   - Time-based         │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### Data Protection

- **Encryption at Rest**: SQLite database encryption
- **Encryption in Transit**: HTTPS/TLS for all communications
- **API Key Management**: Secure storage and rotation
- **Input Validation**: Comprehensive schema validation
- **Rate Limiting**: Protection against abuse and DoS
- **Audit Logging**: Complete activity tracking

---

## 📊 Monitoring & Observability

### Metrics Collection

```python
# Key metrics tracked
class SystemMetrics:
    - query_response_time_ms
    - query_success_rate
    - cache_hit_rate
    - api_request_count
    - error_rate_by_type
    - active_users
    - system_resource_usage
```

### Health Checks

```python
# Health check endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": app.version,
        "services": {
            "ncbi_api": await check_ncbi_connectivity(),
            "cache": await check_cache_status(),
            "nlp": await check_nlp_models()
        }
    }
```

---

## 🚀 Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────────────────────┐
│                 Development Setup                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Local Python │   Docker Compose│   VS Code               │
│   - venv        │   - All services│   - Dev container       │
│   - Hot reload  │   - Databases   │   - Extensions          │
│   - Debug mode  │   - Monitoring  │   - Debugging           │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### Production Environment

```
┌─────────────────────────────────────────────────────────────┐
│                 Production Stack                            │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Container     │   Load Balancer │   Monitoring            │
│   - Docker      │   - Nginx       │   - Prometheus          │
│   - Multi-stage │   - SSL/TLS     │   - Grafana             │
│   - Health check│   - Rate limit  │   - Alerting            │
└─────────────────┴─────────────────┴─────────────────────────┘
```

---

*This architecture document serves as the technical blueprint for OmicsOracle. Update it as the system evolves.*
