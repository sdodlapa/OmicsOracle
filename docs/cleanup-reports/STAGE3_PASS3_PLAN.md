# Stage 3 Pass 3 - Planning Document

**Date**: October 13, 2025
**Status**: Planning
**Target**: Remove redundant client wrappers and configuration (~300 LOC)

---

## Context

### Stage 3 Progress So Far:
- **Pass 1**: -534 LOC (duplicate preprocessing + SearchAgent)
- **Pass 2**: -1,199 LOC (nested pipelines → SearchOrchestrator)
- **Total**: -1,733 LOC (69% of 2,500 LOC goal)

### Stage 3 Goal:
Remove all redundant and duplicate code from the search/pipeline architecture.
- **Target**: 2,500 LOC reduction
- **Remaining**: 767 LOC needed
- **Pass 3 Target**: ~300 LOC

---

## Analysis Areas

### 1. Redundant Client Wrappers

**Question**: Do we have wrapper classes that just delegate to underlying clients?

Let me check:
- `lib/geo/` - GEOClient (direct NCBI integration)
- `lib/publications/clients/` - PubMedClient, OpenAlexClient, GoogleScholarClient
- `lib/citations/clients/` - Citation-specific clients

**Look for**: Classes that just wrap other classes without adding value.

### 2. Duplicate Configuration Classes

**Known configs**:
- `SearchConfig` (new, simplified)
- `UnifiedSearchConfig` (old, archived)
- `PublicationSearchConfig` (publications module)
- `PubMedConfig`, `GoogleScholarConfig`, etc.

**Question**: Can we consolidate or simplify?

### 3. Unused Pipeline Components

After removing nested pipelines, check for:
- Unused imports
- Orphaned helper functions
- Dead code paths

### 4. Duplicate Models

**Known models**:
- `SearchResult` (new, in lib/search/models.py)
- `SearchResult` (old, in lib/geo/models.py for GEO client)
- Publication models scattered across modules

**Question**: Can we unify?

---

## Investigation Plan

### Step 1: Find Redundant Wrappers
```bash
# Find all client classes
grep -r "class.*Client" omics_oracle_v2/lib/ --include="*.py"

# Check for delegation patterns (methods that just call another method)
grep -A 10 "def.*self\)" omics_oracle_v2/lib/*/client*.py
```

### Step 2: Find Configuration Overlap
```bash
# List all config classes
grep -r "class.*Config" omics_oracle_v2/lib/ --include="*.py"

# Check for duplicate fields
```

### Step 3: Find Unused Code
```bash
# Check for unused imports
flake8 omics_oracle_v2/lib/ | grep F401

# Check for functions not called
```

### Step 4: Identify Duplicate Models
```bash
# Find all model definitions
grep -r "class.*Result\|class.*Input\|class.*Output" omics_oracle_v2/lib/ --include="*.py"
```

---

## Expected Findings

Based on the codebase structure, I expect to find:

### 1. **Redundant Query Processing** (~100 LOC)
- Multiple query analyzers/optimizers
- Duplicate NER/entity extraction logic
- Overlapping query builders

### 2. **Configuration Bloat** (~80 LOC)
- Multiple config classes with overlapping fields
- Unused config options after pipeline removal
- Config classes that could be dataclasses or dicts

### 3. **Wrapper Classes** (~70 LOC)
- Client wrappers that just delegate
- Adapter classes that don't adapt anything
- Unnecessary abstraction layers

### 4. **Duplicate Models** (~50 LOC)
- Multiple SearchResult definitions
- Duplicate Publication/Dataset models
- Redundant response builders

---

## Cleanup Strategy

### Phase 1: Investigation
1. Run code analysis tools
2. Map all client/config/model classes
3. Identify actual usage vs. defined functionality
4. Document findings

### Phase 2: Prioritization
1. Rank by LOC reduction potential
2. Rank by risk (low/medium/high)
3. Identify quick wins vs. complex refactors

### Phase 3: Implementation
1. Start with low-risk, high-value items
2. Remove unused imports/code first
3. Consolidate configs
4. Merge duplicate models
5. Remove wrapper classes

### Phase 4: Validation
1. Run all tests
2. Check API endpoints
3. Verify no regressions

### Phase 5: Documentation & Commit
1. Document changes
2. Update architecture diagrams
3. Commit with detailed message

---

## Risk Assessment

### Low Risk (Safe to remove):
- Unused imports (F401 errors)
- Dead code (unreferenced functions)
- Duplicate constant definitions

### Medium Risk (Needs testing):
- Configuration consolidation
- Model unification
- Helper function removal

### High Risk (Needs careful review):
- Client wrapper removal
- Query processing changes
- Breaking API changes

---

## Success Criteria

- ✅ Remove ~300 LOC
- ✅ No functionality regressions
- ✅ All tests passing
- ✅ API endpoints working
- ✅ Code cleaner and more maintainable

---

## Next Steps

1. Run investigation tools
2. Create detailed findings document
3. Get approval for changes
4. Implement in phases
5. Test thoroughly
6. Commit and document

---

**Status**: Ready to start investigation phase
