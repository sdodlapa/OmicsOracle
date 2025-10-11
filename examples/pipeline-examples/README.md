# Pipeline Examples

Real-world examples of using OmicsOracle's pipelines for different research workflows.

---

## 📋 Available Examples

### GEO Citation Pipeline

**File**: `geo-citation-pipeline.py`

**What it demonstrates**:
- Complete GEO → Citations → PDFs workflow
- Dataset metadata extraction
- Citation discovery
- Full-text URL collection

**Use case**: Finding all publications citing a specific GEO dataset

**Run it**:
```bash
python examples/pipeline-examples/geo-citation-pipeline.py
```

---

### Optimized Pipeline (Full)

**File**: `optimized-pipeline-full.py`

**What it demonstrates**:
- Query optimization (1 → 18 datasets)
- Citation discovery improvements
- Full-text URL collection
- Performance metrics tracking

**Use case**: End-to-end optimized citation collection

**Run it**:
```bash
python examples/pipeline-examples/optimized-pipeline-full.py
```

**Expected results**:
- Optimized query finding 18x more datasets
- Higher citation counts
- Better full-text coverage

---

### Query Preprocessing

**File**: `query-preprocessing.py`

**What it demonstrates**:
- Query optimization techniques
- Synonym expansion
- Field-specific searches
- Boolean query construction

**Use case**: Improving search precision and recall

**Run it**:
```bash
python examples/pipeline-examples/query-preprocessing.py
```

---

### Comprehensive GEO Pipeline

**File**: `geo-pipeline-comprehensive.py`

**What it demonstrates**:
- Complete GEO dataset analysis
- Metadata extraction
- Quality scoring
- Multi-step validation

**Use case**: Full-featured dataset discovery and analysis

---

### GEO Pipeline with Citations

**File**: `geo-pipeline-with-citations.py`

**What it demonstrates**:
- GEO dataset + citation integration
- Publication linking
- Cross-referencing
- Citation metrics

**Use case**: Finding datasets AND their citing publications

---

### Improved Pipeline

**File**: `improved-pipeline.py`

**What it demonstrates**:
- Recent pipeline improvements
- Performance optimizations
- Error handling
- Fallback strategies

---

## 🎯 Choosing the Right Pipeline

Not sure which example to use? See our [Pipeline Decision Guide](../../docs/pipelines/PIPELINE_DECISION_GUIDE.md) for:

- **Quick decision tree** (5 questions)
- **Comparison matrix** (all 5 pipelines)
- **Detailed guides** with code examples
- **Common workflows**

### Quick Reference

| Your Goal | Use This Example |
|-----------|------------------|
| Find publications citing a GEO dataset | `geo-citation-pipeline.py` |
| Search for datasets by topic (optimized) | `optimized-pipeline-full.py` |
| Improve search query quality | `query-preprocessing.py` |
| Full dataset + citation analysis | `geo-pipeline-with-citations.py` |
| Test all pipeline features | `geo-pipeline-comprehensive.py` |

---

## 🔧 Common Setup

All pipeline examples require:

1. **Environment variables**:
   ```bash
   NCBI_EMAIL=your.email@example.com
   NCBI_API_KEY=your_ncbi_api_key
   ```

2. **Optional (for AI features)**:
   ```bash
   OPENAI_API_KEY=your_openai_key
   ```

3. **For institutional networks**:
   ```bash
   SSL_VERIFY=false
   ```

---

## 📊 Expected Performance

Based on the optimized pipeline:
- Query optimization: **18x more datasets** found
- Citation discovery: **100+ citations** per relevant dataset
- Full-text coverage: **60-80%** with institutional access
- End-to-end time: **2-5 seconds** (cached), **10-30 seconds** (uncached)

---

## 📖 Learn More

- [Pipeline Decision Guide](../../docs/pipelines/PIPELINE_DECISION_GUIDE.md) - Comprehensive guide
- [GEO Client Documentation](../../docs/current-2025-10/features/GEO_CLIENT.md)
- [Citation Pipeline Guide](../../docs/phase6-consolidation/)
