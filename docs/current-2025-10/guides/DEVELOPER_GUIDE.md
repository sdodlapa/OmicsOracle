# OmicsOracle Developer Guide

**Version:** 2.0
**Date:** June 25, 2025
**Status:** Consolidated Documentation

---

## 🌟 Vision & Philosophy

### Vision Statement
OmicsOracle transforms the complexity of genomics metadata discovery into an intuitive, intelligent experience. We envision a future where researchers can query vast genomics databases using natural language and receive precise, actionable insights within seconds.

**"Democratizing genomics data discovery through intelligent AI-powered summarization"**

### Mission Statement
To build the world's most intelligent and reliable GEO metadata summarization system that:
- **Empowers researchers** with natural language access to genomics data
- **Accelerates scientific discovery** through intelligent metadata extraction
- **Maintains the highest standards** of accuracy, reliability, and performance
- **Serves the scientific community** with open, accessible tools

---

## 🏛️ Core Principles

### 1. Scientific Rigor & Accuracy
**Principle**: Every feature must meet scientific standards of accuracy and reproducibility.

**Implementation**:
- Minimum 95% accuracy for metadata extraction and term mapping
- Comprehensive validation against known GEO datasets
- Transparent methodology with detailed documentation
- Version-controlled ontology mappings and model weights
- Scientific peer review integration for major releases

### 2. Reliability & Robustness
**Principle**: Rock-solid stability for mission-critical research workflows.

**Implementation**:
- 99.9% uptime target with graceful degradation
- Comprehensive error handling and recovery mechanisms
- Rate limiting and circuit breaker patterns for external APIs
- Automated backup and disaster recovery procedures
- Extensive monitoring and alerting systems

### 3. Performance & Scalability
**Principle**: Fast response times that scale with research demands.

**Implementation**:
- Sub-5-second response times for standard queries
- Horizontal scaling capability for high-traffic periods
- Intelligent caching strategies for frequently accessed data
- Asynchronous processing for long-running tasks
- Resource-efficient algorithms and data structures

### 4. Modularity & Extensibility
**Principle**: Clean, modular architecture that evolves with scientific needs.

**Implementation**:
- Plugin architecture for new data sources and ontologies
- Clear separation of concerns between components
- Well-defined APIs for inter-component communication
- Support for multiple output formats and integrations
- Easy addition of new genomics assay types and platforms

### 5. Open Science & Transparency
**Principle**: Open development practices that benefit the entire scientific community.

**Implementation**:
- Open-source codebase with permissive licensing
- Public API documentation and examples
- Transparent algorithm descriptions and validation metrics
- Community contribution guidelines and governance
- Regular community feedback integration

### 6. Quality-First Development
**Principle**: Quality is built in, not tested in.

**Implementation**:
- Test-driven development (TDD) for critical components
- Continuous integration with automated quality gates
- Code review requirements for all changes
- Automated security scanning and dependency management
- Performance regression testing

---

## 🛠️ Development Environment Setup

### Prerequisites
- Python 3.11 or higher
- Node.js 18+ (for frontend development)
- Docker and Docker Compose
- Git

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd OmicsOracle

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run initial tests
pytest
```

### Docker Development
```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in development mode
docker-compose -f docker-compose.dev.yml up
```

---

## 🛡️ Quality Assurance Framework

### Code Quality Standards

#### 1. Code Style & Formatting
- **Black**: Python code formatting (line length: 80)
- **isort**: Import sorting and organization
- **flake8**: Python linting and style checking
- **mypy**: Static type checking

#### 2. Testing Strategy
```
Testing Pyramid:
┌─────────────────────┐
│   E2E Tests (10%)   │  Full pipeline validation
├─────────────────────┤
│ Integration (20%)   │  Component interaction
├─────────────────────┤
│  Unit Tests (70%)   │  Individual function testing
└─────────────────────┘
```

**Unit Tests**:
- Minimum 90% code coverage for core modules
- Property-based testing for data processing functions
- Mock external dependencies (GEO APIs, LLM services)
- Fast execution (<30 seconds for full unit test suite)

**Integration Tests**:
- Test real GEO API interactions with rate limiting
- Validate ontology mapping services
- End-to-end pipeline testing with sample queries
- Database integration and migration testing

**End-to-End Tests**:
- Full natural language query to result pipeline
- Performance and load testing
- User acceptance criteria validation
- Multi-browser testing for web interfaces

#### 3. Security Standards
- **bandit** for Python security linting
- **safety** for dependency vulnerability scanning
- **semgrep** for custom security rule enforcement
- Regular security audits and penetration testing
- Secure coding practices for API key management

#### 4. Performance Standards
- Response time monitoring for all API endpoints
- Memory usage profiling for data processing functions
- Database query performance optimization
- Automated performance regression detection
- Load testing for production readiness

### Development Workflow

#### Git Workflow
```
main (production-ready)
├── develop (integration branch)
│   ├── feature/geo-parser (feature branch)
│   ├── feature/nlp-enhancement (feature branch)
│   └── hotfix/api-rate-limiting (hotfix branch)
└── release/v1.0.0 (release branch)
```

**Branch Protection Rules**:
- `main`: Requires pull request, 2 approvals, passing CI/CD
- `develop`: Requires pull request, 1 approval, passing tests
- Feature branches: Regular commits, rebase before merge

#### Code Review Process
1. **Self Review**: Author reviews own code before PR
2. **Automated Checks**: All CI/CD checks must pass
3. **Peer Review**: At least one team member review
4. **Domain Expert**: Subject matter expert for complex features
5. **Final Approval**: Maintainer approval for merge

#### Pre-Push Checklist
```bash
# Run comprehensive checks before pushing:
./scripts/pre_push_check.sh

# Manual verification:
pre-commit run --all-files
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
```

---

## 📋 Project Structure

```
OmicsOracle/
├── src/omics_oracle/          # Main application code
│   ├── api/                   # FastAPI endpoints
│   ├── cli/                   # Command-line interface
│   ├── core/                  # Core functionality
│   ├── geo_tools/             # GEO database clients
│   ├── nlp/                   # NLP processing
│   ├── pipeline/              # Main processing pipeline
│   ├── services/              # Business logic services
│   └── web/                   # Web interface
├── tests/                     # Test suites
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── performance/           # Performance tests
│   └── validation/            # Validation tests
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── config/                    # Configuration files
├── data/                      # Data files and cache
└── interfaces/                # Web interface implementations
```

---

## 🔧 Configuration Management

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

---

## 🚀 Quick Development Commands

### Daily Development
```bash
# Start development server
uvicorn src.omics_oracle.api.main:app --reload

# Run tests
pytest                          # All tests
pytest tests/unit/             # Unit tests only
pytest --cov=src/omics_oracle  # With coverage

# Code quality
black .                        # Format code
isort .                        # Sort imports
flake8                         # Lint code
mypy src/                      # Type checking
```

### Building and Deployment
```bash
# Build package
python -m build

# Build Docker image
docker build -t omics-oracle .

# Run production container
docker-compose -f docker-compose.prod.yml up
```

---

## 🔒 ASCII-Only Code Policy

### Rationale & Benefits
- **Cross-platform compatibility**: Ensures code works identically on all operating systems
- **CI/CD reliability**: Prevents pipeline failures due to character encoding issues
- **Terminal compatibility**: Works in all shell environments and terminal emulators
- **Git workflow stability**: Avoids merge conflicts and encoding problems
- **International collaboration**: ASCII works universally across all locales
- **Scientific reproducibility**: Ensures consistent behavior in all environments

### Implementation
- **Automated enforcement**: Pre-commit hooks and CI/CD checks prevent violations
- **Comprehensive coverage**: All code, scripts, configs, and commit messages
- **Exception handling**: Unicode allowed ONLY in markdown documentation (.md/.rst files)
- **Character replacement**: Use ASCII alternatives for common Unicode symbols
- **Error reporting**: Clear violation messages with specific character codes and locations

---

## 🤝 Contributing

### Getting Started
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Set up development environment (see setup instructions above)
4. Make your changes following our coding standards
5. Write tests for new functionality
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Contribution Guidelines
- Follow our code quality standards
- Include tests for all new features
- Update documentation as needed
- Follow the ASCII-only policy for code files
- Write clear, descriptive commit messages
- Ensure all CI/CD checks pass

### Issue Reporting
- Use clear, descriptive titles
- Include steps to reproduce the issue
- Provide system information and versions
- Include relevant logs and error messages
- Tag issues appropriately (bug, enhancement, documentation, etc.)

---

## 📊 Success Metrics

### Development Metrics
- **Code Coverage**: >90% for core modules
- **Test Pass Rate**: 100% for all environments
- **Security Vulnerabilities**: 0 high/critical issues
- **Performance**: <5s response time for standard queries
- **Documentation Coverage**: All public APIs documented

### Quality Metrics
- **Bug Escape Rate**: <2% of issues reach production
- **Code Review Coverage**: 100% of changes reviewed
- **Technical Debt**: Monitored and actively reduced
- **Accessibility**: WCAG 2.1 AA compliance for web interfaces
- **Security**: Regular audits and vulnerability assessments

---

*This guide serves as the single source of truth for OmicsOracle development. Keep it updated as the project evolves.*
