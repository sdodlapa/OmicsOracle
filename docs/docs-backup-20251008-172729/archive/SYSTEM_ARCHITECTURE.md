# OmicsOracle System Architecture

**Version:** 1.0.0
**Date:** June 22, 2025
**Status:** Phase 1.2 Implementation

## Architecture Overview

OmicsOracle follows a modular, layered architecture designed for scalability, maintainability, and scientific rigor.

## System Components

### 1. Core Layer

```text
src/omics_oracle/core/
├── __init__.py
├── config.py          # Configuration management
├── exceptions.py      # Custom exception classes
├── logging.py         # Logging infrastructure
├── models.py          # Data models and schemas
├── types.py           # Type definitions
└── validators.py      # Input validation
```

### 2. GEO Tools Layer

```text
src/omics_oracle/geo_tools/
├── __init__.py
├── ncbi_client.py     # NCBI API client (entrezpy)
├── geo_parser.py      # GEO data parsing (GEOparse)
├── sra_client.py      # SRA integration (pysradb)
├── metadata_extractor.py  # Metadata extraction
└── validators.py      # GEO-specific validation
```

### 3. NLP Processing Layer

```text
src/omics_oracle/nlp/
├── __init__.py
├── preprocessor.py    # Text preprocessing
├── summarizer.py      # AI summarization
├── classifier.py      # Content classification
├── entity_extractor.py  # Scientific entity extraction
└── models.py         # NLP model definitions
```

### 4. API Layer

```text
src/omics_oracle/api/
├── __init__.py
├── app.py            # FastAPI application
├── endpoints/
│   ├── __init__.py
│   ├── search.py     # Search endpoints
│   ├── metadata.py   # Metadata endpoints
│   └── health.py     # Health check endpoints
├── models/           # Pydantic models
└── middleware/       # API middleware
```

### 5. CLI Layer

```text
src/omics_oracle/cli/
├── __init__.py
├── main.py           # CLI entry point
├── commands/
│   ├── __init__.py
│   ├── search.py     # Search commands
│   ├── config.py     # Configuration commands
│   └── validate.py   # Validation commands
└── utils.py          # CLI utilities
```

### 6. Database Layer

```text
src/omics_oracle/database/
├── __init__.py
├── models.py         # SQLAlchemy models
├── connection.py     # Database connection
├── migrations/       # Database migrations
└── repositories/     # Data access layer
```

## Data Flow Architecture

```text
User Query → CLI/API → Query Processor → GEO Client → NCBI APIs
                                            ↓
Results ← Summarizer ← NLP Pipeline ← Metadata Extractor ← GEO Data
```

## Configuration System

### Environment-based Configuration

- `config/development.yml` - Development settings
- `config/production.yml` - Production settings
- `config/testing.yml` - Testing settings
- `.env` - Environment variables

### Configuration Schema

```yaml
# Base configuration structure
database:
  url: "${DATABASE_URL}"
  pool_size: 10

ncbi:
  api_key: "${NCBI_API_KEY}"
  email: "${NCBI_EMAIL}"
  rate_limit: 3

nlp:
  model: "en_core_sci_sm"
  batch_size: 32
  max_tokens: 512

logging:
  level: "INFO"
  format: "json"
  file: "logs/omics_oracle.log"
```

## Quality Assurance Architecture

### Testing Strategy

- **Unit Tests:** Component-level testing
- **Integration Tests:** API and database testing
- **End-to-End Tests:** Complete workflow testing
- **Performance Tests:** Load and stress testing

### Quality Gates

1. **Code Quality:** Black, isort, flake8
2. **Type Safety:** mypy type checking
3. **Security:** bandit security scanning
4. **ASCII Compliance:** Custom ASCII enforcer
5. **Test Coverage:** pytest-cov (>90% target)

## Deployment Architecture

### Development Environment

- Local SQLite database
- Local file storage
- Development API server
- Mock external services

### Production Environment

- PostgreSQL database
- Redis caching layer
- Load balancer
- Containerized deployment

## API Schema Design

### Core Endpoints

```text
GET /api/v1/search
POST /api/v1/search/advanced
GET /api/v1/metadata/{geo_id}
GET /api/v1/health
```

### Request/Response Models

```python
class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=10, le=100)

class MetadataResponse(BaseModel):
    geo_id: str
    title: str
    summary: str
    organism: str
    platform: str
    samples: int
    created_date: datetime
```

## Error Handling Strategy

### Exception Hierarchy

```text
OmicsOracleException
├── ValidationError
├── ConfigurationError
├── GEOClientError
├── NLPProcessingError
└── DatabaseError
```

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid search query",
    "details": {
      "field": "query",
      "reason": "Query must be at least 3 characters"
    }
  }
}
```

## Performance Considerations

### Caching Strategy

- **API Response Caching:** Redis for search results
- **Database Query Caching:** SQLAlchemy query cache
- **NLP Model Caching:** In-memory model loading

### Rate Limiting

- **NCBI API:** 3 requests per second
- **API Endpoints:** 100 requests per minute per IP
- **Database Connections:** Connection pooling

## Security Architecture

### Authentication & Authorization

- API key authentication for production
- Role-based access control
- Request signing for sensitive operations

### Data Protection

- Input sanitization and validation
- SQL injection prevention
- XSS protection
- Rate limiting and DDoS protection

## Monitoring & Observability

### Logging Strategy

- Structured JSON logging
- Request/response logging
- Error tracking and alerting
- Performance metrics

### Health Checks

- Database connectivity
- External API availability
- System resource utilization
- Cache health status

## Next Steps (Phase 1.2)

1. **Implement Core Configuration System**
2. **Create Base Models and Types**
3. **Set up Logging Infrastructure**
4. **Create Database Schema**
5. **Implement Basic CLI Interface**
6. **Set up Development Environment**

---

This architecture document will be updated as we progress through implementation phases.
