# OmicsOracle System Architecture

**Version:** 3.0
**Date:** October 8, 2025
**Status:** Production Architecture (Phase 4 Complete)
**Major Changes:** Added 5 AI Agents, GPT-4 Integration, Authentication System, Dashboard

---

## 🏗️ Architecture Overview

OmicsOracle follows a ### 5. GEO Tools Layer

```
src/omics_oracle/geo_tools/### 7. API Layer (Enhanced - Phase 4)

```
src/omics_oracle/api/
├── __init__.py
├── main.py           # FastAPI application
├──### 9. CLI Layer

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

---

### 10. Web Interface Layer── auth.py       # Authentication endpoints (NEW)
│   ├── agents.py     # Agent endpoints (NEW)
│   ├── search.py     # Search endpoints
│   ├── analysis.py   # Analysis endpoints
│   ├── export.py     # Export endpoints
│   └── config.py     # Configuration endpoints
└── middleware/
    ├── auth.py       # JWT validation middleware (NEW)
    └── rate_limit.py # Rate limiting middleware
```

**Responsibilities:**
- RESTful API endpoints
- Request/response validation
- JWT authentication and authorization
- Rate limiting per user/IP
- API documentation (OpenAPI/Swagger)

**New API Routes (Phase 4):**
```
/api/auth/*           # Authentication
  - POST /register    # User registration
  - POST /login       # User login
  - POST /refresh     # Token refresh
  - GET /me           # Current user

/api/agents/*         # AI Agent operations
  - POST /search      # Search agent
  - POST /analyze     # Analysis agent (GPT-4)
  - POST /qa          # Q&A agent
  - POST /quality     # Quality predictions
  - POST /recommend   # Recommendations

/api/search/*         # Dataset search
  - GET /datasets     # Search datasets
  - GET /datasets/{id} # Get dataset details
  - POST /advanced    # Advanced search

/api/analysis/*       # Analysis operations
  - POST /citations   # Citation extraction
  - POST /biomarkers  # Biomarker detection
  - POST /trends      # Research trends

/api/export/*         # Data export
  - POST /csv         # CSV export
  - POST /json        # JSON export
  - POST /pdf         # PDF report
```

---

### 8. Dashboard Layer (NEW - Phase 4)
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

---

### 6. NLP Processing Layerrchitecture designed for scalability, maintainability, and scientific rigor. The system is built with microservices principles while maintaining simplicity for research workflows.

### High-Level Architecture (Phase 4 - Multi-Agent System)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          User Interfaces                                │
├─────────────────┬─────────────────┬─────────────────┬───────────────────┤
│   Dashboard     │   Web Interface │   API Interface │  CLI Interface    │
│   (Real-time)   │   (React/Flask) │   (FastAPI)     │  (Click-based)    │
│   - Search      │   - Interactive │   - RESTful     │  - Batch          │
│   - AI Analysis │   - Viz         │   - Webhooks    │  - Automation     │
│   - Auth UI     │   - Export      │   - Docs        │  - Scripts        │
└─────────────────┴─────────────────┴─────────────────┴───────────────────┘
                                      │
┌─────────────────────────────────────────────────────────────────────────┐
│                        Application Layer                                │
├─────────────────┬─────────────────┬─────────────────┬───────────────────┤
│   Auth Service  │   Query Router  │   Rate Limiter  │  Session Manager  │
│   - JWT Tokens  │   - Intent      │   - Per-user    │  - User state     │
│   - Register    │   - Routing     │   - Per-IP      │  - Preferences    │
│   - Login       │   - Validation  │   - Per-endpoint│  - History        │
│   - Refresh     │   - Transform   │   - NCBI limits │  - Analytics      │
└─────────────────┴─────────────────┴─────────────────┴───────────────────┘
                                      │
┌─────────────────────────────────────────────────────────────────────────┐
│                       Multi-Agent Service Layer                         │
├─────────────────┬─────────────────┬─────────────────┬───────────────────┤
│   Query Agent   │   Search Agent  │ Analysis Agent  │  Quality Agent    │
│   - Entity      │   - GEO Query   │   - GPT-4       │  - Predictions    │
│   - Extraction  │   - 20-30s perf │   - 13-15s perf │  - Scoring        │
│   - Intent      │   - Caching     │   - Insights    │  - Validation     │
│   - Parameters  │   - Filtering   │   - QA/Summary  │  - Thresholds     │
├─────────────────┴─────────────────┴─────────────────┼───────────────────┤
│  Recommendation Agent              │  LLM Service (GPT-4)                │
│  - Related datasets                │  - OpenAI API                       │
│  - Research trends                 │  - Prompt Engineering               │
│  - Similar studies                 │  - Token Management                 │
│  - Citation networks               │  - Context Injection                │
└────────────────────────────────────┴─────────────────────────────────────┘
                                      │
┌─────────────────────────────────────────────────────────────────────────┐
│                      Core Services Layer                                │
├─────────────────┬─────────────────┬─────────────────┬───────────────────┤
│   GEO Service   │   NLP Service   │  Cache Service  │  Monitoring       │
│   - NCBI API    │   - Embeddings  │   - Redis       │  - Metrics        │
│   - Parsing     │   - Similarity  │   - SQLite      │  - Logging        │
│   - Validation  │   - Extraction  │   - File cache  │  - Health         │
└─────────────────┴─────────────────┴─────────────────┴───────────────────┘
                                      │
┌─────────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                      │
├─────────────────┬─────────────────┬─────────────────┬───────────────────┤
│   GEO Database  │   User Database │   Cache Store   │  Config + Logs    │
│   (External)    │   (SQLite)      │   (Redis/File)  │  (YAML/JSON)      │
│   - Datasets    │   - Users       │   - Queries     │  - Settings       │
│   - Metadata    │   - Sessions    │   - Results     │  - API keys       │
│   - Publications│   - Tokens      │   - Summaries   │  - Audit logs     │
└─────────────────┴─────────────────┴─────────────────┴───────────────────┘
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

---

### 2. Authentication & Authorization Layer (NEW - Phase 4)

```
src/omics_oracle/auth/
├── __init__.py
├── jwt_handler.py     # JWT token management
├── user_manager.py    # User CRUD operations
├── middleware.py      # Auth middleware
└── models.py          # User and session models
```

**Responsibilities:**
- JWT token generation and validation
- User registration and login
- Password hashing (bcrypt)
- Session management
- Protected route middleware
- Token refresh mechanism

**API Endpoints:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User authentication
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/me` - Current user info
- `POST /api/auth/logout` - Session termination

**Performance:**
- Login: <500ms
- Token validation: <50ms
- Token refresh: <200ms

---

### 3. Multi-Agent System (NEW - Phase 4)

```
src/omics_oracle/agents/
├── __init__.py
├── base_agent.py      # Base agent class
├── query_agent.py     # Query understanding & entity extraction
├── search_agent.py    # GEO dataset search
├── analysis_agent.py  # GPT-4 powered analysis
├── quality_agent.py   # Data quality prediction
├── recommendation_agent.py  # Dataset recommendations
└── orchestrator.py    # Agent coordination
```

#### 3.1 Query Agent
**Responsibilities:**
- Natural language query parsing
- Scientific entity extraction (genes, diseases, organisms)
- Query intent classification
- Parameter extraction and normalization

**Example:**
```python
# Input: "Find breast cancer RNA-seq datasets in humans"
# Output:
{
    "entities": {
        "disease": ["breast cancer"],
        "technology": ["RNA-seq"],
        "organism": ["Homo sapiens"]
    },
    "intent": "dataset_search",
    "filters": {
        "study_type": "Expression profiling by high throughput sequencing",
        "organism": "Homo sapiens"
    }
}
```

#### 3.2 Search Agent
**Responsibilities:**
- GEO dataset query construction
- Advanced filtering (organism, platform, date range)
- Result ranking and scoring
- Caching for performance

**Performance:**
- Average search time: 20-30 seconds
- Cache hit rate: >60%
- Results per query: 10-100 datasets

**API Endpoint:**
- `POST /api/agents/search` - Execute search with filters

#### 3.3 Analysis Agent (GPT-4 Powered)
**Responsibilities:**
- Dataset insight generation
- Scientific summary creation
- Q&A about datasets
- Research context extraction

**Performance:**
- Average analysis time: 13-15 seconds
- Token usage: ~2000 tokens per analysis
- Model: GPT-4 (OpenAI)

**API Endpoints:**
- `POST /api/agents/analyze` - Analyze dataset(s)
- `POST /api/agents/qa` - Answer questions about datasets

**Example:**
```python
# Input: GSE12345
# Output:
{
    "summary": "This RNA-seq study investigates...",
    "key_findings": [...],
    "methodology": "...",
    "relevance_score": 0.92,
    "suggested_applications": [...]
}
```

#### 3.4 Data Quality Agent
**Responsibilities:**
- Dataset quality scoring (0-1 scale)
- Completeness assessment
- Metadata quality validation
- Sample size evaluation

**Quality Metrics:**
- Metadata completeness
- Sample count
- Publication status
- Data availability

**API Endpoint:**
- `POST /api/agents/quality` - Get quality predictions

#### 3.5 Recommendation Agent
**Responsibilities:**
- Related dataset discovery
- Citation network analysis
- Research trend identification
- Similar study suggestions

**API Endpoint:**
- `POST /api/agents/recommend` - Get recommendations

---

### 4. LLM Integration Layer (NEW - Phase 4)

```
src/omics_oracle/llm/
├── __init__.py
├── openai_client.py   # OpenAI API integration
├── prompt_templates.py # Prompt engineering
├── token_manager.py   # Token usage tracking
└── retry_handler.py   # Error handling & retries
```

**Responsibilities:**
- OpenAI API client management
- GPT-4 model integration
- Prompt engineering and template management
- Token usage tracking and optimization
- Retry logic with exponential backoff
- Error handling and fallback strategies

**Configuration:**
```python
LLM_CONFIG = {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 30,
    "retry_attempts": 3,
    "rate_limit": {
        "requests_per_minute": 20,
        "tokens_per_minute": 40000
    }
}
```

**Performance Monitoring:**
- Token usage per request
- Response latency
- Error rate
- Cost tracking

---

### 5. GEO Tools Layer

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

### 6. NLP Processing Layer

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

---

### 7. API Layer (Enhanced - Phase 4)

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

### 8. Dashboard Layer (NEW - Phase 4)

```
src/omics_oracle/dashboard/
├── __init__.py
├── app.py            # Streamlit dashboard application
├── pages/
│   ├── login.py      # Login/registration page
│   ├── search.py     # Real-time search interface
│   ├── analysis.py   # AI analysis interface
│   ├── results.py    # Results visualization
│   └── settings.py   # User settings
├── components/
│   ├── auth.py       # Auth UI components
│   ├── search_form.py # Search interface components
│   ├── result_card.py # Result display components
│   └── charts.py     # Visualization components
└── utils/
    ├── api_client.py # Backend API client
    └── state.py      # Session state management
```

**Responsibilities:**
- Real-time dataset search interface
- AI-powered analysis dashboard
- User authentication UI
- Result visualization and export
- Session state management
- Responsive design

**Features:**
- **Authentication:** Login/register with JWT
- **Search:** Real-time search with advanced filters
  - Organism selector
  - Platform selector
  - Date range picker
  - Quality threshold slider
- **AI Analysis:** GPT-4 powered insights
  - Dataset summaries
  - Q&A interface
  - Quality predictions
  - Recommendations
- **Visualization:**
  - Result cards with metadata
  - Quality score indicators
  - Publication links
  - Export options (CSV, JSON, PDF)

**Performance:**
- Page load: <2s
- Search results: 20-30s (cached: <1s)
- AI analysis: 13-15s
- Responsive updates via WebSocket (future)

---

### 9. CLI Layer

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

### Multi-Agent Query Processing Pipeline (Phase 4)

```
1. User Authentication (NEW)
   ├── Login/Register via Dashboard or API
   ├── JWT token generation
   ├── Token validation on protected routes
   └── Session management

2. User Input
   ├── Dashboard: Interactive search form with filters
   ├── API: JSON-formatted query with auth header
   ├── Web: Form-based or natural language
   └── CLI: Natural language query

3. Query Agent Processing (NEW)
   ├── Natural language parsing
   ├── Entity extraction (genes, diseases, organisms)
   ├── Query intent classification
   ├── Parameter normalization
   └── Filter construction

4. Search Agent Execution (NEW)
   ├── Cache lookup for existing results (Redis/SQLite)
   ├── GEO query construction with advanced filters
   ├── NCBI API requests with rate limiting
   ├── Result parsing and validation
   ├── Result ranking and scoring
   └── Cache storage (60-minute TTL)
   └── Performance: 20-30 seconds (cached: <1s)

5. Data Quality Agent Assessment (NEW)
   ├── Metadata completeness scoring
   ├── Sample count evaluation
   ├── Publication status check
   ├── Data availability verification
   └── Quality score (0-1) calculation

6. Analysis Agent Processing (GPT-4) (NEW)
   ├── Dataset context preparation
   ├── Prompt engineering and template selection
   ├── GPT-4 API request (with retry logic)
   ├── Insight generation and summarization
   ├── Key findings extraction
   ├── Token usage tracking
   └── Performance: 13-15 seconds

7. Recommendation Agent (NEW)
   ├── Related dataset discovery
   ├── Citation network analysis
   ├── Similar study identification
   └── Research trend analysis

8. Response Generation
   ├── Multi-agent result aggregation
   ├── Format-specific output (JSON/HTML/CSV)
   ├── Quality metrics inclusion
   ├── AI insights integration
   ├── Caching of processed results
   ├── Response validation
   └── Delivery to user interface (Dashboard/API/Web)

9. Post-Processing
   ├── User activity logging
   ├── Performance metrics collection
   ├── Token usage tracking (GPT-4)
   ├── Cache optimization
   └── Analytics and monitoring
```

### Agent Orchestration Flow

```
User Query
    │
    ▼
┌─────────────────┐
│  Query Agent    │  (Entity extraction, intent classification)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Search Agent   │  (GEO search: 20-30s)
└────────┬────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Quality  │  │ Analysis │  │ Recommend│  │  Cache   │
   │  Agent   │  │  Agent   │  │  Agent   │  │  Store   │
   │          │  │ (GPT-4)  │  │          │  │          │
   │  <1s     │  │ 13-15s   │  │  <2s     │  │  <100ms  │
   └──────────┘  └──────────┘  └──────────┘  └──────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Response Builder│
              └────────┬────────┘
                       │
                       ▼
                  User Interface
```

### Caching Strategy (Enhanced - Phase 4)

```
┌─────────────────────────────────────────────────────────────────┐
│                  Multi-Level Caching System                     │
├─────────────────┬─────────────────┬───────────────────────────┤
│   L1: Redis     │   L2: SQLite    │   L3: File System         │
│   (In-Memory)   │   (Persistent)  │   (Long-term)             │
├─────────────────┼─────────────────┼───────────────────────────┤
│ - Search cache  │ - User data     │ - Raw GEO data            │
│ - Session state │ - AI summaries  │ - Export files            │
│ - Auth tokens   │ - Metadata      │ - Logs & metrics          │
│ - Query results │ - Analytics     │ - Backup data             │
│                 │ - Quality scores│ - Historical results      │
│ TTL: 60 min     │ TTL: 24 hours   │ TTL: 30 days              │
│ Hit rate: 60%+  │ Hit rate: 80%+  │ Archive only              │
└─────────────────┴─────────────────┴───────────────────────────┘
```

**Cache Keys Strategy:**
```python
# Search cache key
f"search:{hash(query_params)}"

# AI analysis cache key
f"analysis:gpt4:{dataset_id}:{version}"

# Quality prediction cache key
f"quality:{dataset_id}"

# User session key
f"session:{user_id}:{token_id}"
```

**Cache Invalidation:**
- Time-based expiration:
  - Search results: 60 minutes
  - AI summaries: 24 hours
  - Quality scores: 24 hours
  - Auth tokens: 7 days
- Version-based invalidation for configuration changes
- Manual cache clearing via admin API
- Intelligent cache warming for popular queries
- LRU eviction for memory management

---

## 🔧 Configuration Management

### Environment-Based Configuration (Enhanced - Phase 4)

```yaml
# config/base.yml - Base configuration
app:
  name: "OmicsOracle"
  version: "3.0.0"  # Updated for Phase 4
  debug: false

# Authentication configuration (NEW)
auth:
  jwt_secret_key: "${JWT_SECRET_KEY}"  # From environment
  jwt_algorithm: "HS256"
  access_token_expire_minutes: 60
  refresh_token_expire_days: 7
  bcrypt_rounds: 12

# LLM configuration (NEW)
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"  # From environment
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
  retry_attempts: 3
  rate_limit:
    requests_per_minute: 20
    tokens_per_minute: 40000

# Agent configuration (NEW)
agents:
  query_agent:
    enabled: true
    entity_extraction: true
  search_agent:
    enabled: true
    cache_ttl_minutes: 60
    max_results: 100
  analysis_agent:
    enabled: true
    model: "gpt-4"
    cache_ttl_hours: 24
  quality_agent:
    enabled: true
    min_score: 0.5
  recommendation_agent:
    enabled: true
    max_recommendations: 10

# config/development.yml - Development overrides
app:
  debug: true
  log_level: "DEBUG"

auth:
  access_token_expire_minutes: 1440  # 24 hours for dev

llm:
  model: "gpt-3.5-turbo"  # Cheaper for testing
  temperature: 0.5

ncbi:
  rate_limit: 1  # Slower for development
  timeout: 30

# config/production.yml - Production overrides
app:
  log_level: "INFO"

auth:
  access_token_expire_minutes: 60
  require_email_verification: true

llm:
  model: "gpt-4"
  rate_limit:
    requests_per_minute: 20

ncbi:
  rate_limit: 3  # NCBI recommended limit
  timeout: 10

cache:
  redis:
    host: "${REDIS_HOST}"
    port: 6379
    db: 0
    ttl_minutes: 60

logging:
  level: "INFO"
  format: "json"
  handlers:
    - file
    - syslog
  performance_tracking: true
  token_usage_tracking: true  # NEW - Track GPT-4 costs
```

---

## 🛡️ Security Architecture (Enhanced - Phase 4)

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layers                            │
├─────────────────┬─────────────────┬───────────────────────────┤
│   Auth Layer    │   Rate Limiting │   Access Control          │
│   (NEW)         │   (Enhanced)    │   (Enhanced)              │
├─────────────────┼─────────────────┼───────────────────────────┤
│ - JWT tokens    │ - Per IP        │ - Role-based (RBAC)       │
│ - Password hash │ - Per user      │ - Resource-level          │
│ - Token refresh │ - Per endpoint  │ - Time-based              │
│ - Session mgmt  │ - NCBI limits   │ - Token validation        │
│                 │ - LLM limits    │ - Protected routes        │
└─────────────────┴─────────────────┴───────────────────────────┘
```

### JWT Token Structure

```json
{
  "access_token": {
    "user_id": "uuid",
    "email": "user@example.com",
    "role": "researcher",
    "exp": "timestamp",
    "iat": "timestamp"
  },
  "refresh_token": {
    "user_id": "uuid",
    "exp": "timestamp (7 days)",
    "iat": "timestamp"
  }
}
```

### Protected Route Middleware

```python
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Validate JWT token on protected routes
    - Skip: /api/auth/login, /api/auth/register, /health
    - Require: All /api/agents/*, /api/search/*, /api/analysis/*
    """
    if request.url.path.startswith("/api/agents"):
        token = request.headers.get("Authorization")
        if not token:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing authentication token"}
            )
        # Validate JWT and attach user to request
        user = await validate_token(token)
        request.state.user = user

    return await call_next(request)
```

### Data Protection

- **Encryption at Rest**:
  - SQLite database encryption (SQLCipher)
  - Encrypted environment variables
  - Secure API key storage
- **Encryption in Transit**:
  - HTTPS/TLS 1.3 for all communications
  - Certificate pinning for production
- **Password Security**:
  - bcrypt hashing (12 rounds)
  - Minimum password strength requirements
  - No plaintext storage
- **API Key Management**:
  - Secure storage in environment variables
  - Key rotation support
  - Separate keys per environment
- **Input Validation**:
  - Pydantic schema validation
  - SQL injection prevention
  - XSS protection
- **Rate Limiting** (Enhanced):
  - Per-user limits: 100 requests/hour
  - Per-IP limits: 200 requests/hour
  - Per-endpoint limits: Varies by cost
  - NCBI API: 3 requests/second
  - OpenAI API: 20 requests/minute, 40K tokens/minute
- **Audit Logging**:
  - All authentication events
  - All API requests with user context
  - LLM token usage per user
  - Failed access attempts
  - Security events

---

## 📊 Monitoring & Observability (Enhanced - Phase 4)

### Metrics Collection

```python
# Key metrics tracked (Enhanced for Phase 4)
class SystemMetrics:
    # Performance metrics
    query_response_time_ms: float
    search_agent_time_ms: float  # NEW - Typically 20-30s
    analysis_agent_time_ms: float  # NEW - Typically 13-15s
    query_success_rate: float
    cache_hit_rate: float

    # Usage metrics
    api_request_count: int
    active_users: int
    concurrent_sessions: int

    # Agent metrics (NEW)
    agent_invocations_by_type: Dict[str, int]
    agent_success_rate_by_type: Dict[str, float]
    agent_avg_latency_by_type: Dict[str, float]

    # LLM metrics (NEW)
    llm_requests_count: int
    llm_tokens_used: int
    llm_cost_usd: float
    llm_avg_response_time_ms: float
    llm_error_rate: float

    # Auth metrics (NEW)
    login_success_rate: float
    token_refresh_count: int
    failed_auth_attempts: int

    # Error tracking
    error_rate_by_type: Dict[str, float]
    error_rate_by_endpoint: Dict[str, float]

    # System resources
    cpu_usage_percent: float
    memory_usage_mb: float
    disk_usage_mb: float
    cache_size_mb: float
```

### Health Checks (Enhanced)

```python
# Health check endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "3.0.0",
        "services": {
            "ncbi_api": await check_ncbi_connectivity(),
            "cache": await check_cache_status(),
            "database": await check_database_connection(),
            "nlp": await check_nlp_models(),
            "openai_api": await check_openai_connectivity(),  # NEW
            "redis": await check_redis_connection(),  # NEW
        },
        "agents": {  # NEW
            "query_agent": {"status": "active", "uptime": "99.9%"},
            "search_agent": {"status": "active", "avg_latency": "25s"},
            "analysis_agent": {"status": "active", "avg_latency": "14s"},
            "quality_agent": {"status": "active", "avg_latency": "0.5s"},
            "recommendation_agent": {"status": "active", "avg_latency": "1.5s"}
        },
        "performance": {  # NEW
            "cache_hit_rate": 0.65,
            "avg_search_time": 24.5,
            "avg_analysis_time": 13.8,
            "tokens_used_today": 150000,
            "estimated_cost_today_usd": 3.75
        }
    }

@app.get("/health/detailed")  # NEW - Detailed health check
@require_auth(role="admin")
async def detailed_health_check():
    return {
        "system": await get_system_metrics(),
        "agents": await get_agent_metrics(),
        "llm": await get_llm_metrics(),
        "cache": await get_cache_metrics(),
        "database": await get_database_metrics(),
        "alerts": await get_active_alerts()
    }
```

### Performance Dashboards (NEW)

**Grafana Dashboards:**
1. **Agent Performance Dashboard**
   - Agent response times (line chart)
   - Agent invocation counts (bar chart)
   - Agent success rates (gauge)
   - Agent error distribution (pie chart)

2. **LLM Usage Dashboard**
   - Token usage over time (area chart)
   - Cost tracking (line chart)
   - Request rate (line chart)
   - Error rate (gauge)

3. **User Activity Dashboard**
   - Active users (gauge)
   - Login/registration trends (line chart)
   - Session duration (histogram)
   - Failed auth attempts (bar chart)

4. **Cache Performance Dashboard**
   - Hit rate by cache level (gauge)
   - Cache size trends (line chart)
   - Eviction rate (line chart)
   - Most cached queries (table)

---

## 🚀 Deployment Architecture (Enhanced - Phase 4)

### Development Environment

```
┌─────────────────────────────────────────────────────────────────┐
│                   Development Setup                             │
├─────────────────┬─────────────────┬───────────────────────────┤
│   Local Python │   Docker Compose│   VS Code                  │
│   - venv        │   - All services│   - Dev container          │
│   - Hot reload  │   - Redis       │   - Extensions             │
│   - Debug mode  │   - SQLite      │   - Debugging              │
│                 │   - Dashboard   │   - Copilot integration    │
└─────────────────┴─────────────────┴───────────────────────────┘

Docker Compose Services:
- app: FastAPI backend
- dashboard: Streamlit dashboard
- redis: Cache layer
- prometheus: Metrics collection
- grafana: Visualization
```

### Production Environment

```
┌─────────────────────────────────────────────────────────────────┐
│                   Production Stack                              │
├─────────────────┬─────────────────┬───────────────────────────┤
│   Container     │   Load Balancer │   Monitoring               │
│   - Docker      │   - Nginx       │   - Prometheus             │
│   - Multi-stage │   - SSL/TLS 1.3 │   - Grafana                │
│   - Health check│   - Rate limit  │   - Alerting               │
│   - Auto-scale  │   - WAF         │   - Log aggregation        │
└─────────────────┴─────────────────┴───────────────────────────┘

Infrastructure:
- Container Orchestration: Docker Swarm or Kubernetes
- Reverse Proxy: Nginx with SSL termination
- Cache: Redis cluster (HA setup)
- Database: SQLite (single node) or PostgreSQL (if scaling)
- Secrets: Vault or AWS Secrets Manager
- Logging: ELK stack or CloudWatch
- Monitoring: Prometheus + Grafana
```

### Deployment Workflow

```
1. Development
   ├── Local development with hot reload
   ├── Unit tests with pytest
   ├── Integration tests
   └── Pre-commit hooks (Black, isort, flake8)

2. CI/CD Pipeline (GitHub Actions)
   ├── Run automated tests
   ├── Lint and format check
   ├── Security scan (Snyk, Bandit)
   ├── Build Docker images
   ├── Push to container registry
   └── Deploy to staging

3. Staging Environment
   ├── Full system testing
   ├── Load testing
   ├── Security testing
   ├── Performance benchmarking
   └── User acceptance testing

4. Production Deployment
   ├── Blue-green deployment
   ├── Health check validation
   ├── Gradual traffic shift
   ├── Monitoring and alerts
   └── Rollback capability
```

### Scalability Considerations (Phase 4)

**Horizontal Scaling:**
- **API Layer**: Stateless, can scale to N instances
- **Dashboard**: Can run multiple instances with sticky sessions
- **Redis**: Cluster mode for high availability
- **Agents**: Stateless, can be parallelized

**Performance Targets:**
- **Search Agent**: 20-30s (target: <20s with optimization)
- **Analysis Agent**: 13-15s (GPT-4 bound, minimal optimization)
- **Concurrent users**: 100+ (with proper caching)
- **Requests per second**: 50+ (with load balancing)

**Cost Optimization:**
- **Caching**: 60%+ cache hit rate reduces API costs
- **LLM batching**: Batch multiple analyses to reduce overhead
- **GPT-3.5 fallback**: For simpler queries to reduce cost
- **Result reuse**: Share analysis results across users

---

## 🔮 Phase 5 Roadmap Integration

### Planned Enhancements

**Sprint 1: GEO Features Enhancement (Oct 8-22, 2025)**
- Advanced filtering UI
- Organism selector with autocomplete
- Platform selector with categories
- Quality threshold slider
- Dataset comparison tool

**Sprint 2: AI Capabilities Extension (Oct 22-Nov 5, 2025)**
- Multi-dataset analysis
- Comparative analysis
- Research gap identification
- Hypothesis generation

**Sprint 3: Visualization & Export (Nov 5-19, 2025)**
- Interactive charts (Plotly)
- Network visualizations
- PDF report generation
- Citation network graphs

**Sprint 4: Collaboration Features (Nov 19-Dec 3, 2025)**
- Shared workspaces
- Result annotations
- Team collaboration
- Export sharing

---

*This architecture document reflects the production-ready Phase 4 system with 5 AI agents, GPT-4 integration, authentication, and real-time dashboard. Updated October 8, 2025.*
