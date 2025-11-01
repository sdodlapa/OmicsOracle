# Phase 2: Rigorous Package Consolidation Plan

**Date:** October 15, 2025  
**Status:** 🟡 PLANNING  
**Prerequisites:** ✅ Phase 1 Complete

---

## 🎯 Objectives

Reduce the remaining 12 directories to ~8 well-organized, purposeful packages by:
1. Merging small, related directories
2. Resolving code duplication
3. Creating clear domain boundaries

---

## 📊 Current State (Post-Phase 1)

```
omics_oracle_v2/lib/
├── analysis/                11 files  ← Keep
├── infrastructure/           4 files  ← MERGE candidate  
├── llm/                      4 files  ← EVALUATE
├── performance/              3 files  ← MERGE candidate
├── pipelines/               54 files  ← Keep (main codebase)
├── query_processing/        10 files  ← Keep
├── registry/                 2 files  ← MERGE candidate
├── search_engines/          11 files  ← Keep
├── search_orchestration/     4 files  ← MERGE candidate
├── storage/                  7 files  ← Keep
└── utils/                    2 files  ← Keep (core)
```

---

## 🔍 Consolidation Candidates

### **Merge Group 1: Infrastructure & Monitoring**
**Target:** `infrastructure/` (4 files) + `performance/` (3 files) → `monitoring/` (7 files)

**Rationale:**
- Both handle system-level concerns (health checks, metrics, performance)
- Natural grouping: infrastructure monitoring + performance tracking
- Creates cohesive monitoring/observability package

**Investigation needed:**
- [ ] Check if infrastructure/ has health check endpoints
- [ ] Check if performance/ has metrics/profiling code
- [ ] Verify no circular imports with pipelines/

---

### **Merge Group 2: Search Components**
**Target:** `search_orchestration/` (4 files) → `search_engines/` (11→15 files)

**Rationale:**
- Both handle search-related functionality
- Orchestration likely coordinates search engines
- Reduces search-related package fragmentation

**Investigation needed:**
- [ ] What does search_orchestration actually orchestrate?
- [ ] Does it depend on search_engines or vice versa?
- [ ] Check for circular import risks

**Alternative:** Merge into `pipelines/` if orchestration is pipeline-specific

---

### **Merge Group 3: Registry**
**Target:** `registry/` (2 files) → **WHERE?**

**Options:**
1. Merge into `storage/` if it's a data registry
2. Merge into `infrastructure/` if it's service registry
3. Merge into `utils/` if it's a pattern registry

**Investigation needed:**
- [ ] What does registry/ register? (services, data sources, pipelines?)
- [ ] Check import patterns to determine best merge target

---

### **Evaluate: LLM Package**
**Target:** `llm/` (4 files) → Keep or merge into `analysis/`?

**Keep if:**
- Growing rapidly with new LLM integrations
- Core business logic (significant LLM features)
- Clear domain separation from analysis

**Merge if:**
- Static code (no recent changes)
- Only used for analysis/enrichment
- No plans for major LLM expansion

**Investigation needed:**
- [ ] Check git history - active development or static?
- [ ] Usage patterns - core feature or helper?
- [ ] Roadmap - planned LLM expansion?

---

## 🔧 Critical: Resolve Client Duplication

**Issue discovered:** PubMed/OpenAlex clients implemented in TWO places:

```
search_engines/citations/
├── pubmed.py       ← Original implementation
└── openalex.py     ← Original implementation

pipelines/citation_discovery/clients/
├── pubmed.py       ← Duplicate! (actively used)
└── openalex.py     ← Duplicate! (actively used)
```

**Decision required:**
1. **Option A:** Keep in `search_engines/citations/` (canonical location)
   - Move pipelines to import from search_engines
   - Delete pipelines/citation_discovery/clients/
   
2. **Option B:** Keep in `pipelines/citation_discovery/clients/` (co-location)
   - Update search_engines to re-export from pipelines
   - Prefer if clients are pipeline-specific implementations

**Investigation needed:**
- [ ] Compare implementations - are they identical or diverged?
- [ ] Check which version is newer/better maintained
- [ ] Evaluate: domain-driven (search_engines) vs. co-location (pipelines)

---

## 📋 Investigation Checklist

### For Each Small Directory:

```bash
# 1. Check actual usage
grep -r "from omics_oracle_v2.lib.{DIRECTORY}" omics_oracle_v2/

# 2. Check what it imports (dependencies)
grep -r "^from omics_oracle_v2.lib" omics_oracle_v2/lib/{DIRECTORY}/

# 3. Check git activity
git log --since="2024-01-01" --oneline omics_oracle_v2/lib/{DIRECTORY}/

# 4. List file purposes
ls -lh omics_oracle_v2/lib/{DIRECTORY}/
```

### For Each Merge Candidate:

- [ ] No circular import risks
- [ ] Semantic coherence (related functionality)
- [ ] No excessive coupling created
- [ ] Clear migration path for imports

---

## 🎯 Target Structure (8-9 directories)

```
omics_oracle_v2/lib/
├── analysis/              11 files  ← Data analysis, enrichment
├── llm/                    4 files  ← LLM integration (if keeping)
├── monitoring/             7 files  ← Infrastructure + Performance merged
├── pipelines/             54 files  ← Main orchestration logic
├── query_processing/      10 files  ← Query parsing, validation
├── search_engines/        15 files  ← Search clients + orchestration
├── storage/                9 files  ← Storage + Registry merged
└── utils/                  2 files  ← Core utilities
```

**Total:** 8 directories (down from 12, 33% reduction from Phase 1's 18)

---

## ✅ Success Criteria

- [ ] No more than 8-10 top-level directories
- [ ] All directories have clear, single responsibility
- [ ] No small (<5 files) directories without strong justification
- [ ] Zero broken imports in production code
- [ ] All tests passing
- [ ] Documentation updated

---

## 🚀 Execution Strategy

### Step 1: Investigation (1-2 hours)
Run analysis scripts for each consolidation candidate

### Step 2: Plan Review (30 min)
Review findings, finalize merge decisions

### Step 3: Execute Merges (2-3 hours)
- One merge at a time
- Update imports immediately
- Test after each merge

### Step 4: Validation (1 hour)
- Run full test suite
- Verify production functionality
- Update documentation

### Step 5: Commit & Document (30 min)
- Git commit with detailed messages
- Update architecture docs
- Create migration guide if needed

---

## 🛡️ Risk Mitigation

**Before ANY merge:**
1. ✅ Create git branch: `lib-consolidation-phase2`
2. ✅ Archive original to `archive/lib-phase2-backup/`
3. ✅ Run tests before and after each change
4. ✅ Maintain rollback capability

**If issues arise:**
- Immediate rollback available
- Archive preserves original code
- Git history allows bisecting problems

---

## 📝 Notes

- Phase 1 eliminated 6 directories safely
- Phase 2 targets 4 more (33% additional reduction)
- Combined reduction: 10/18 directories = 56% cleanup
- Final structure: Clean, maintainable, Pythonic

---

*Next: Begin Phase 2 Investigation*
