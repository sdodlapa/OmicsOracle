# Sprint Demos

Demonstrations of features developed in each sprint.

---

## 📋 Available Demos

### Sprint 1: Parallel Metadata Fetching

**File**: `sprint1-parallel-fetching.py`

**What it demonstrates**:
- Parallel batch fetching vs sequential (10x faster)
- Cache effectiveness (50x faster on cache hits)
- End-to-end search performance (90% improvement: 25s → 2.5s)

**Run it**:
```bash
python examples/sprint-demos/sprint1-parallel-fetching.py
```

**Expected output**:
- Performance comparison metrics
- Cache hit/miss statistics
- Overall speedup measurements

---

### OpenAlex Integration

**File**: `openalex-integration.py`

**What it demonstrates**:
- OpenAlex API integration
- Publication metadata fetching
- Citation network analysis
- Cross-referencing with GEO datasets

**Run it**:
```bash
python examples/sprint-demos/openalex-integration.py
```

---

### OpenAlex Search

**File**: `openalex-search.py`

**What it demonstrates**:
- Advanced search using OpenAlex API
- Filtering by publication type
- Citation count analysis
- Author affiliation data

**Run it**:
```bash
python examples/sprint-demos/openalex-search.py
```

---

## 🔧 Prerequisites

- NCBI API key and email configured
- OpenAI API key (for some features)
- Active internet connection
- Virtual environment activated

---

## 📊 Performance Metrics

Sprint 1 improvements:
- **Parallel fetching**: 10x faster than sequential
- **Caching**: 50x faster on cache hits
- **End-to-end**: 90% faster overall

---

## 📖 Learn More

- [Pipeline Decision Guide](../../docs/pipelines/PIPELINE_DECISION_GUIDE.md)
- [API Reference](../../docs/API_REFERENCE.md)
