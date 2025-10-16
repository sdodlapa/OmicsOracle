# TODO List - Post-Production Features

**Last Updated:** October 16, 2025

---

## 🎯 Current Priority: Core Functionality

### ⚠️ Critical (P0) - Must Complete Before Production
- [ ] **Citation counts displaying correctly**
  - Issue: Dashboard shows incorrect citation counts
  - Status: In progress
  - Blocker: Yes

- [ ] **PDF downloads working reliably**
  - Issue: PDF download functionality needs validation
  - Status: In progress
  - Blocker: Yes

- [ ] **AI analysis functioning properly**
  - Issue: AI analysis pipeline needs testing
  - Status: In progress
  - Blocker: Yes

- [ ] **System stability in production**
  - Test with real user traffic
  - Monitor error rates
  - Validate auto-discovery performance

---

## 📋 Planned Features (P1-P2) - Post-Production

### 1. 🔬 Execution Path Tracing & Profiling System (P2)
**Status:** Planned  
**Estimated Effort:** 1-2 weeks  
**Document:** [`EXECUTION_PATH_TRACING_PLAN.md`](./EXECUTION_PATH_TRACING_PLAN.md)

**What it does:**
- Automatically track execution paths through the system
- Identify frequently used code (hot paths)
- Profile performance bottlenecks
- Detect error-prone paths
- Find unused/dead code

**Why wait:**
- Requires stable baseline system
- Need real production data for meaningful insights
- Core features must work correctly first
- Avoid premature optimization

**When to implement:**
- ✅ All P0 features complete
- ✅ System stable in production
- ✅ Error rates <5%
- ✅ Real user traffic established

---

### 2. ⚡ Additional Performance Optimizations (P2)
**Status:** Planned  
**Document:** `docs/EXECUTION_TREE_OPTIMIZATION.md` (Phase 2 section)

**Optimizations to implement:**

#### Negative Result Caching
- Cache 404s for 24 hours
- **Impact:** 15-20% reduction in API calls
- **Effort:** 2 hours

#### Request Deduplication
- Prevent duplicate requests in parallel threads
- **Impact:** 15-30% fewer duplicate requests
- **Effort:** 4 hours

#### Database Connection Pooling
- Use SQLAlchemy connection pooling
- **Impact:** Lower latency, better scalability
- **Effort:** 4 hours

#### PostgreSQL Migration (if needed)
- Migrate from SQLite to PostgreSQL
- **Impact:** 2-5x faster for concurrent access
- **Effort:** 1-2 days
- **Trigger:** When concurrent users > 50

---

### 3. 🧹 Code Quality Improvements (P3)
**Status:** Low priority

#### Pydantic V1 → V2 Migration
- Migrate `@validator` to `@field_validator`
- **Files affected:**
  - `omics_oracle_v2/lib/search_engines/citations/models.py:89`
  - `omics_oracle_v2/lib/pipelines/citation_discovery/clients/config.py:89,160`
- **Impact:** Remove deprecation warnings
- **Effort:** 1-2 hours

---

## 📊 Progress Tracking

### Completed ✅
- [x] Dashboard bugs fixed (Oct 2025)
- [x] Auto-discovery implemented (Oct 2025)
- [x] Performance optimizations (50x dataset enrichment speedup)
- [x] Database indexes optimized
- [x] Citation discovery timeout added
- [x] Execution tree analysis (DFS/BFS)

### In Progress 🔄
- [ ] Citation count accuracy
- [ ] PDF download reliability
- [ ] AI analysis functionality

### Planned 📋
- [ ] Execution path tracing system
- [ ] Additional performance optimizations
- [ ] Code quality improvements

---

## 🎯 Next Steps

1. **Focus on P0 items** (citation counts, PDF downloads, AI analysis)
2. **Test thoroughly** before production deployment
3. **Monitor production** for stability
4. **Review this list** once production is stable
5. **Prioritize P1/P2 features** based on user feedback and data

---

## 📝 Notes

- This TODO list tracks post-production enhancements
- Current focus: Get core functionality working reliably
- All planned features have detailed documentation
- Implementation deferred until system is production-ready
- Revisit quarterly or after major milestones

