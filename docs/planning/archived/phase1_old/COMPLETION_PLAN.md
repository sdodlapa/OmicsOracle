# OmicsOracle - Completion & Cleanup Plan

**Date:** October 6, 2025  
**Status:** Ready to Execute  
**Objective:** Complete Phase 1, Cleanup, then Plan Multi-Agent System

---

## Overview

Based on comprehensive code audit, we have:
- ✅ **Phase 1: 95% complete** (all code built and integrated)
- ❌ **Missing:** GEO dataset vector index (1-2 hours to generate)
- ⚠️ **Documentation:** 484 files, needs cleanup

**Strategy:** Complete → Cleanup → Plan (in that order)

---

## Part 1: Complete Phase 1 Semantic Search (TODAY - 3 hours)

### Task 1.1: Check Database & Cache (15 min)

```bash
# Check what GEO datasets are available
sqlite3 omics_oracle.db "SELECT COUNT(*) FROM datasets;"
ls -lh data/cache/

# Expected: Some cached GEO datasets in JSON format
# If empty, we'll need to fetch datasets first
```

### Task 1.2: Generate GEO Dataset Embeddings (1-2 hours)

**Prerequisites:**
- OpenAI API key set in environment
- Database has GEO datasets cached

```bash
# Set API key
export OPENAI_API_KEY="your-key-here"

# Create vector database directory
mkdir -p data/vector_db

# Run embedding script
python -m omics_oracle_v2.scripts.embed_geo_datasets \
    --cache-dir data/cache \
    --output data/vector_db/geo_index.faiss \
    --batch-size 100 \
    --verbose

# Expected output:
# [1/4] Loading datasets from data/cache...
# [OK] Loaded 1234 datasets
# [2/4] Configuring embedding service...
#   Provider: openai
#   Model: text-embedding-3-small
# [3/4] Embedding 1234 datasets...
#   Batch size: 100
# [4/4] Saving index to data/vector_db/geo_index.faiss...
# [OK] Index saved successfully
```

**Cost Estimate:**
- 1000 datasets × 500 tokens avg = 500K tokens
- text-embedding-3-small: $0.02 / 1M tokens
- **Total cost: ~$0.01** (negligible)

**Time:**
- 1000 datasets / 100 per batch = 10 batches
- ~5-10 seconds per batch = 1-2 minutes total
- With caching: Faster on reruns

### Task 1.3: Test Semantic Search (30 min)

```bash
# Start development server
./start_dev_server.sh

# Server runs on http://localhost:8000
```

**Test Steps:**

1. **Open UI:** http://localhost:8000/static/semantic_search.html

2. **Enable Semantic Search:**
   - Check "Enable Semantic Search" toggle

3. **Test Query:**
   ```
   Query: "ATAC-seq chromatin accessibility analysis"
   ```

4. **Verify Features:**
   - ✅ Query expansion shown (synonyms: "chromatin accessibility", "ATAC sequencing", etc.)
   - ✅ Semantic scores displayed (0.0-1.0)
   - ✅ Reranked results (cross-encoder scores)
   - ✅ Faster than traditional GEO search

5. **Compare Modes:**
   - Disable toggle → Traditional keyword search
   - Enable toggle → Semantic search
   - Compare result quality

### Task 1.4: Update Documentation (30 min)

Create comprehensive semantic search guide:

```bash
# Files to update:
# 1. READY_TO_USE.md - Add semantic search section
# 2. API_REFERENCE.md - Document enable_semantic flag
# 3. Create new SEMANTIC_SEARCH_GUIDE.md
```

**Deliverable:** Users can now access fully functional semantic search!

---

## Part 2: Documentation Cleanup (Days 2-3 - 8 hours)

### Task 2.1: Archive Phase Plans (2 hours)

```bash
# Create archive directory
mkdir -p docs/archive/phase-plans-2025-10

# Archive old phase plans
find docs/planning -name "PHASE_*.md" -exec mv {} docs/archive/phase-plans-2025-10/ \;
find docs/plans -name "*PLAN*.md" -exec mv {} docs/archive/phase-plans-2025-10/ \;
find docs/ -name "*ROADMAP*.md" ! -path "*/archive/*" -exec mv {} docs/archive/phase-plans-2025-10/ \;

# Create archive README
cat > docs/archive/phase-plans-2025-10/README.md << 'EOF'
# Archived Phase Plans (October 2025)

These phase plans represent the original development roadmap.
They have been archived because:

1. Phase 0-1 are complete
2. Phase 4 is partially complete
3. Phases 2-3-5-6 are superseded by multi-agent architecture

## What Was Completed:

- **Phase 0:** Configurable ranking (100% - production-ready)
- **Phase 1:** Semantic search (95% - missing only dataset index)
- **Phase 4:** Auth & rate limiting (40% - basic features done)

## Next Steps:

See `/docs/MULTI_AGENT_ROADMAP.md` for the new strategic direction.

**Archived:** October 6, 2025
EOF

# Report
echo "Archived $(ls docs/archive/phase-plans-2025-10/*.md | wc -l) phase plan files"
```

### Task 2.2: Consolidate Core Documentation (3 hours)

**Keep Only Essential Files:**

```bash
# Essential documentation structure:
docs/
├── README.md                           # Main entry point
├── QUICK_START.md                      # 5-minute setup
├── ARCHITECTURE.md                     # System architecture
├── API_REFERENCE.md                    # API documentation
├── SEMANTIC_SEARCH_GUIDE.md            # NEW: How to use semantic search
├── guides/
│   ├── DEVELOPER_GUIDE.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── TESTING_GUIDE.md
├── architecture/                       # Technical details
│   ├── AGENTS.md
│   ├── AUTHENTICATION.md
│   └── SEARCH_PIPELINE.md
└── archive/                           # Historical documents
    ├── phase-plans-2025-10/
    └── analysis-reports/
```

**Files to Archive:**

```bash
# Move analysis reports to archive
mkdir -p docs/archive/analysis-reports
mv docs/reports/*ANALYSIS*.md docs/archive/analysis-reports/
mv docs/reports/*REVIEW*.md docs/archive/analysis-reports/
mv docs/reports/*ASSESSMENT*.md docs/archive/analysis-reports/

# Move old planning documents
mv docs/planning/* docs/archive/phase-plans-2025-10/ 2>/dev/null || true

# Result: ~50 essential files (down from 484)
```

### Task 2.3: Create Consolidated Documentation (2 hours)

**Essential Documents to Create/Update:**

1. **docs/README.md** - Navigation hub
2. **docs/CURRENT_STATE.md** - What works now (October 2025)
3. **docs/SEMANTIC_SEARCH_GUIDE.md** - Complete guide
4. **docs/architecture/SEARCH_PIPELINE.md** - Technical deep-dive

### Task 2.4: Update Root README (1 hour)

```markdown
# OmicsOracle

AI-powered biomedical dataset search with semantic understanding.

## Current Features (October 2025)

✅ **Keyword Search** - GEO database integration
✅ **Semantic Search** - AI-powered with query expansion & reranking  
✅ **AI Analysis** - GPT-4 dataset insights
✅ **Quality Scoring** - 7-dimensional assessment
✅ **Authentication** - JWT-based user management
✅ **Rate Limiting** - Redis-powered quotas

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Add your OPENAI_API_KEY

# 3. Start server
./start_dev_server.sh

# 4. Open browser
# http://localhost:8000/static/semantic_search.html
```

## Documentation

- 📖 [Quick Start Guide](docs/QUICK_START.md)
- 🔍 [Semantic Search Guide](docs/SEMANTIC_SEARCH_GUIDE.md)
- 🏗️ [Architecture Overview](docs/ARCHITECTURE.md)
- 📚 [API Reference](docs/API_REFERENCE.md)
- 🧪 [Testing Guide](docs/guides/TESTING_GUIDE.md)

## What's Next

See [NEXT_STEPS.md](NEXT_STEPS.md) for multi-agent architecture roadmap.
```

---

## Part 3: Post-Cleanup Status (End of Week 1)

### Expected State:

**✅ Functional:**
- Phase 1 semantic search complete and accessible
- All features working and documented
- Clean, navigable documentation

**✅ Documentation:**
- 484 files → ~50 essential files
- Clear architecture documentation
- User-friendly guides
- All old plans archived (not deleted)

**✅ Codebase:**
- No changes needed (already production-ready)
- All tests passing
- Clean architecture

---

## Part 4: Multi-Agent Planning (Week 2 - AFTER cleanup)

**Only start this AFTER Parts 1-3 are complete.**

### Goals for Week 2:

1. **Design Smart Hybrid Architecture**
   - 20% GPT-4 orchestrator (complex queries)
   - 80% BioMedLM on A100 (simple queries)
   - Complexity router logic
   - Rate limit avoidance strategy

2. **Specify Publication Mining Modules**
   - PubMed metadata fetcher
   - Citation network builder
   - PDF download & parsing pipeline
   - LLM analysis integration

3. **Plan GPU Deployment**
   - A100 deployment (on-prem)
   - H100 deployment (GCP with credits)
   - Load balancing strategy
   - Failover & redundancy

4. **Create Master Roadmap**
   - 8-week implementation plan
   - Week-by-week milestones
   - Resource allocation
   - Success metrics

### Deliverables for Week 2:

- `docs/MULTI_AGENT_ARCHITECTURE.md` (final design)
- `docs/PUBLICATION_MINING_SPEC.md` (detailed spec)
- `docs/GPU_DEPLOYMENT_PLAN.md` (infrastructure)
- `docs/8_WEEK_IMPLEMENTATION_ROADMAP.md` (master plan)

---

## Execution Order (Critical!)

```
┌─────────────────────────────────────┐
│  TODAY (3 hours)                    │
│  ✅ Complete Phase 1                │
│  ✅ Test semantic search            │
│  ✅ Update docs                     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Days 2-3 (8 hours)                 │
│  ✅ Archive phase plans             │
│  ✅ Consolidate documentation       │
│  ✅ Create essential guides         │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Week 2 (8 hours)                   │
│  📝 Multi-agent architecture        │
│  📝 Publication mining spec         │
│  📝 GPU deployment plan             │
│  📝 8-week roadmap                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Weeks 3-10 (40-50 hours)           │
│  🚀 Build multi-agent system        │
│  🚀 Deploy to GPUs                  │
│  🚀 Integrate publication mining    │
└─────────────────────────────────────┘
```

**DO NOT SKIP AHEAD!** Each phase builds on the previous.

---

## Success Criteria

### Part 1 Complete When:
- ✅ `data/vector_db/geo_index.faiss` exists
- ✅ Semantic search toggle works in UI
- ✅ Query expansion visible
- ✅ Results show reranking scores
- ✅ Documentation updated

### Part 2 Complete When:
- ✅ ~130 phase plans archived
- ✅ Documentation: 484 → ~50 files
- ✅ All essential docs created/updated
- ✅ Navigation is clear
- ✅ New users can onboard easily

### Part 3 Ready When:
- ✅ Clean repo state
- ✅ All features documented
- ✅ Ready for new development
- ✅ Foundation solid for multi-agent

---

## Risk Mitigation

### If Dataset Embedding Fails:

**Problem:** No GEO datasets in cache

**Solution:**
```bash
# Option 1: Fetch sample datasets
python -m omics_oracle_v2.scripts.fetch_geo_sample --limit 100

# Option 2: Use mock embeddings for testing
python -m omics_oracle_v2.scripts.embed_geo_datasets --provider mock
```

### If OpenAI API Key Issues:

**Problem:** Rate limits or quota exceeded

**Solution:**
- Use smaller batch size: `--batch-size 20`
- Limit datasets: `--limit 500`
- Embeddings are cached - rerunning is fast

### If Cleanup Breaks Links:

**Problem:** Archived docs have broken links

**Solution:**
- Keep archive/ directory in docs/
- Use relative paths in new docs
- Git preserves history - can always revert

---

## Next Session Handoff

**If you need to pause, current state is:**

```bash
# Check what's completed:
ls -lh data/vector_db/geo_index.faiss  # Phase 1 done?
find docs/archive/phase-plans-2025-10 -name "*.md" | wc -l  # Cleanup done?

# Resume from appropriate part:
# - No index file → Start Part 1 (complete Phase 1)
# - Index exists, 484 docs → Start Part 2 (cleanup)
# - ~50 docs, clean → Start Part 3 (multi-agent planning)
```

---

## Estimated Timeline

| Phase | Duration | When | Deliverable |
|-------|----------|------|-------------|
| **Part 1: Complete** | 3 hours | Today | Semantic search working |
| **Part 2: Cleanup** | 8 hours | Days 2-3 | Clean documentation |
| **Part 3: Plan** | 8 hours | Week 2 | Multi-agent roadmap |
| **Part 4: Build** | 40-50h | Weeks 3-10 | Production system |

**Total to completion:** 59-69 hours over 10 weeks

---

## Questions Before Starting?

Before we execute, confirm:

1. ✅ OpenAI API key available?
2. ✅ Okay to archive old phase plans (not delete)?
3. ✅ Ready to test semantic search today?
4. ✅ Multi-agent planning waits until Week 2?

**If all ✅, let's start with Part 1: Complete Phase 1!**
