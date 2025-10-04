# OmicsOracle v2

**Status**: 🚧 Development (Phase 1: Algorithm Extraction)
**Version**: 2.0.0-alpha
**Target**: Multi-Agent Smart Data Summary System

---

## Overview

OmicsOracle v2 is a complete redesign of the biomedical data analysis platform, featuring:

- **Clean Architecture**: Extracted, reusable algorithms with zero legacy dependencies
- **Type Safety**: Full type hints with PEP 561 compliance
- **Dependency Injection**: No global state, everything is configurable and testable
- **Comprehensive Testing**: 80%+ test coverage with unit and integration tests
- **Multi-Agent Ready**: Foundation for Phase 2 agent architecture

---

## Structure

```
omics_oracle_v2/
├── lib/                      # Algorithm library (standalone, reusable)
│   ├── nlp/                 # Biomedical NER and text processing
│   ├── geo/                 # GEO database access
│   └── ai/                  # AI summarization services
├── core/                    # Core infrastructure
│   ├── config.py           # Pydantic-based configuration
│   ├── exceptions.py       # Exception hierarchy
│   └── types.py            # Type definitions
├── tests/                   # Comprehensive test suite
│   ├── unit/               # Unit tests (80%+ coverage)
│   └── integration/        # Integration tests
└── examples/               # Usage examples
```

---

## Development Status

### Phase 1: Algorithm Extraction (Current)

**Goal**: Extract proven algorithms from v1 into clean, standalone libraries

**Progress**:
- [x] Task 1: Project structure setup
- [ ] Task 2: Core infrastructure extraction
- [ ] Task 3: BiomedicalNER extraction
- [ ] Task 4: UnifiedGEOClient extraction
- [ ] Task 5: SummarizationService extraction
- [ ] Task 6: Integration testing
- [ ] Task 7: Documentation & performance

**Target Completion**: October 30, 2025

---

## Quick Start

> **Note**: v2 is under active development. These examples will work as modules are completed.

### Installation

```bash
# Development installation
pip install -e .
```

### Basic Usage

```python
# NER Example (Task 3)
from omics_oracle_v2.lib.nlp import BiomedicalNER

ner = BiomedicalNER()
result = ner.extract_entities("TP53 gene mutations in lung cancer")
for entity in result.entities:
    print(f"{entity.text} ({entity.entity_type})")
```

```python
# GEO Access Example (Task 4)
from omics_oracle_v2.lib.geo import UnifiedGEOClient

client = UnifiedGEOClient()
series = client.get_series("GSE123456")
print(f"{series.title}: {series.sample_count} samples")
```

```python
# AI Summarization Example (Task 5)
from omics_oracle_v2.lib.ai import SummarizationService
from omics_oracle_v2.lib.ai.models import SummaryRequest, SummaryType

summarizer = SummarizationService()
request = SummaryRequest(
    text="Long biomedical text...",
    summary_type=SummaryType.CONCISE
)
response = summarizer.summarize(request)
print(response.summary)
```

---

## Configuration

All services are configurable via Pydantic settings:

```python
from omics_oracle_v2.core.config import Settings

settings = Settings(
    nlp=NLPSettings(model_name="en_core_web_sm"),
    geo=GEOSettings(cache_ttl=3600),
    ai=AISettings(model="gpt-4"),
    debug=True
)
```

Or via environment variables:

```bash
export OMICS_NLP_MODEL_NAME=en_core_web_sm
export OMICS_GEO_CACHE_TTL=3600
export OMICS_AI_MODEL=gpt-4
export OMICS_DEBUG=true
```

---

## Testing

```bash
# Run all tests
pytest omics_oracle_v2/tests/

# Run with coverage
pytest --cov=omics_oracle_v2 --cov-report=html

# Run specific test module
pytest omics_oracle_v2/tests/unit/test_nlp.py
```

---

## Documentation

- **API Reference**: `docs/v2/api/` (auto-generated with Sphinx)
- **Migration Guide**: `docs/MIGRATION_V1_TO_V2.md`
- **Phase 1 Plan**: `docs/planning/PHASE_1_EXTRACTION_PLAN.md`
- **Examples**: `omics_oracle_v2/examples/`

---

## Differences from v1

### Architecture

| Aspect | v1 | v2 |
|--------|-------|-------|
| **Structure** | Monolithic | Modular libraries |
| **Dependencies** | Tightly coupled | Standalone |
| **Configuration** | Global state | Dependency injection |
| **Testing** | Partial | 80%+ coverage |
| **Type Safety** | Partial hints | Full typing |
| **Documentation** | Scattered | Comprehensive |

### Import Changes

```python
# v1 (old)
from src.omics_oracle.nlp.biomedical_ner import BiomedicalNER

# v2 (new)
from omics_oracle_v2.lib.nlp import BiomedicalNER
```

---

## Contributing

Phase 1 development follows strict quality gates:

- ✅ All type hints (mypy strict)
- ✅ PEP 8 compliance (flake8)
- ✅ 80%+ test coverage
- ✅ Docstrings on all public APIs
- ✅ Zero imports from v1 (`src/omics_oracle/`)

See `docs/planning/PHASE_1_EXTRACTION_PLAN.md` for detailed task breakdown.

---

## Roadmap

- **Phase 1** (Weeks 3-4): Algorithm extraction → Clean libraries
- **Phase 2** (Weeks 5-8): Multi-agent architecture → Agent framework
- **Phase 3** (Weeks 9-12): Integration & enhancement → Production system

---

## License

[Your License Here]

---

**Last Updated**: October 2, 2025
**Current Phase**: Phase 1 - Task 1 Complete ✅
