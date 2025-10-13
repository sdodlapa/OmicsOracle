# Repository Cleanup Plan
**Date:** October 13, 2025
**Purpose:** Consolidate and organize documentation and redundant files

## 📊 Current State Analysis

### Root Directory Documents (30+ .md files)
The root has accumulated many planning, phase, and status documents that should be organized:

**Phase Documentation (Move to `docs/history/phases/`):**
- `PHASE1_COMPLETE.md`
- `PHASE1_FINAL_STATUS.md`
- `PHASE2B_COMPLETE.md`
- `PHASE2B_FLOW_REORGANIZATION.md`
- `PHASE2B_PHASE3_SUMMARY.md`
- `PHASE2B_PROGRESS.md`
- `PHASE2B_STEP8_COMPLETE.md`
- `PHASE2B_VALIDATION_REPORT.md`
- `PHASE2_CLEANUP_SUMMARY.md`
- `PHASE3_NEXT_STEPS.md`
- `PHASE3_TEST_VALIDATION_REPORT.md`

**Week Documentation (Move to `docs/history/week3/`):**
- `WEEK3_COMPLETE_SUMMARY.md`
- `WEEK3_DAY1_CACHE_OPTIMIZATION_PLAN.md`
- `WEEK3_DAY2_GEO_PARALLELIZATION_PLAN.md`
- `WEEK3_DAYS1-2_COMPLETION_SUMMARY.md`

**Architecture Analysis (Move to `docs/architecture/analysis/`):**
- `ARCHITECTURE_ANALYSIS_REPORT.md`
- `ARCHITECTURE_FLOW_DIAGRAM.md`
- `MANUAL_ARCHITECTURE_VERIFICATION.md`

**Flow Analysis (Move to `docs/architecture/flows/`):**
- `ACTUAL_FLOW_ANALYSIS.md`
- `COMPLETE_FLOW_ANALYSIS.md`
- `END_TO_END_FLOW_ANALYSIS.md`
- `FLOW_DIAGRAM.md`
- `FLOW_FILE_MAPPING.md`
- `README_FLOW_ANALYSIS.md`

**Cleanup/Planning Documents (Move to `docs/planning/cleanup/`):**
- `CLEANUP_PLAN_DETAILED.md`
- `CLEANUP_SUMMARY.md`
- `CODE_CLEANUP_PLAN.md`
- `QUICK_CLEANUP_ACTIONS.md`
- `STAGE_BY_STAGE_CLEANUP_PLAN.md`

**Stage Reports (Move to `docs/history/stages/`):**
- `STAGE_1_TESTING_REPORT.md`
- `STAGE_2_ANALYSIS.md`

**Migration/Layer Documentation (Move to `docs/architecture/`):**
- `MIGRATION_GUIDE_PHASE2B.md`
- `LAYER_4_AND_6_EXPLAINED.md`

**Comprehensive Reviews (Move to `docs/reports/`):**
- `COMPREHENSIVE_CODEBASE_REVIEW.md`

**Keep in Root (Active Status):**
- `README.md` ✅ Main documentation
- `CURRENT_STATUS.md` ✅ Current state
- `NEXT_STEPS.md` ✅ Active planning

## 📁 Proposed Organization Structure

```
docs/
├── history/                          # Historical documentation
│   ├── phases/                       # Phase completion reports
│   │   ├── phase1/
│   │   ├── phase2/
│   │   └── phase3/
│   ├── week3/                        # Week 3 optimization work
│   └── stages/                       # Stage-by-stage reports
├── architecture/                     # Architecture docs (existing)
│   ├── analysis/                     # Architecture analysis reports
│   └── flows/                        # Flow diagrams and analysis
├── planning/                         # Planning docs (existing)
│   └── cleanup/                      # Cleanup plans and summaries
└── reports/                          # Comprehensive reports (existing)
```

## 🎯 Execution Plan

### Step 1: Create New Directory Structure
```bash
mkdir -p docs/history/phases/phase1
mkdir -p docs/history/phases/phase2
mkdir -p docs/history/phases/phase3
mkdir -p docs/history/week3
mkdir -p docs/history/stages
mkdir -p docs/architecture/analysis
mkdir -p docs/architecture/flows
mkdir -p docs/planning/cleanup
```

### Step 2: Move Phase Documents
```bash
# Phase 1
git mv PHASE1_COMPLETE.md docs/history/phases/phase1/
git mv PHASE1_FINAL_STATUS.md docs/history/phases/phase1/

# Phase 2
git mv PHASE2B_COMPLETE.md docs/history/phases/phase2/
git mv PHASE2B_FLOW_REORGANIZATION.md docs/history/phases/phase2/
git mv PHASE2B_PHASE3_SUMMARY.md docs/history/phases/phase2/
git mv PHASE2B_PROGRESS.md docs/history/phases/phase2/
git mv PHASE2B_STEP8_COMPLETE.md docs/history/phases/phase2/
git mv PHASE2B_VALIDATION_REPORT.md docs/history/phases/phase2/
git mv PHASE2_CLEANUP_SUMMARY.md docs/history/phases/phase2/
git mv MIGRATION_GUIDE_PHASE2B.md docs/history/phases/phase2/

# Phase 3
git mv PHASE3_NEXT_STEPS.md docs/history/phases/phase3/
git mv PHASE3_TEST_VALIDATION_REPORT.md docs/history/phases/phase3/
```

### Step 3: Move Week 3 Documents
```bash
git mv WEEK3_COMPLETE_SUMMARY.md docs/history/week3/
git mv WEEK3_DAY1_CACHE_OPTIMIZATION_PLAN.md docs/history/week3/
git mv WEEK3_DAY2_GEO_PARALLELIZATION_PLAN.md docs/history/week3/
git mv WEEK3_DAYS1-2_COMPLETION_SUMMARY.md docs/history/week3/
```

### Step 4: Move Architecture Documents
```bash
# Architecture analysis
git mv ARCHITECTURE_ANALYSIS_REPORT.md docs/architecture/analysis/
git mv MANUAL_ARCHITECTURE_VERIFICATION.md docs/architecture/analysis/
git mv COMPREHENSIVE_CODEBASE_REVIEW.md docs/architecture/analysis/
git mv LAYER_4_AND_6_EXPLAINED.md docs/architecture/

# Flow analysis
git mv ARCHITECTURE_FLOW_DIAGRAM.md docs/architecture/flows/
git mv ACTUAL_FLOW_ANALYSIS.md docs/architecture/flows/
git mv COMPLETE_FLOW_ANALYSIS.md docs/architecture/flows/
git mv END_TO_END_FLOW_ANALYSIS.md docs/architecture/flows/
git mv FLOW_DIAGRAM.md docs/architecture/flows/
git mv FLOW_FILE_MAPPING.md docs/architecture/flows/
git mv README_FLOW_ANALYSIS.md docs/architecture/flows/
```

### Step 5: Move Cleanup/Planning Documents
```bash
git mv CLEANUP_PLAN_DETAILED.md docs/planning/cleanup/
git mv CLEANUP_SUMMARY.md docs/planning/cleanup/
git mv CODE_CLEANUP_PLAN.md docs/planning/cleanup/
git mv QUICK_CLEANUP_ACTIONS.md docs/planning/cleanup/
git mv STAGE_BY_STAGE_CLEANUP_PLAN.md docs/planning/cleanup/
```

### Step 6: Move Stage Reports
```bash
git mv STAGE_1_TESTING_REPORT.md docs/history/stages/
git mv STAGE_2_ANALYSIS.md docs/history/stages/
```

### Step 7: Create Index Files
Create `README.md` files in each new directory explaining contents.

### Step 8: Update References
Search for and update any cross-references to moved files.

## 📝 Files to Keep in Root

### Essential (Keep)
- `README.md` - Main project documentation
- `CURRENT_STATUS.md` - Active status tracking
- `NEXT_STEPS.md` - Active planning

### Configuration (Keep)
- `pyproject.toml`
- `requirements*.txt`
- `Makefile`
- `docker-compose*.yml`
- `Dockerfile*`
- `.gitignore`
- `.pre-commit-config.yaml`
- etc.

## 🗑️ Potential Cleanup

### Redundant Files to Review
- `chrome_cookies.py` - Is this still used?
- `setup_logging.py` - Should this be in `omics_oracle_v2/`?
- `test_output.log` - Should be in `.gitignore`
- `omics_oracle.db` - Should be in `.gitignore` or `data/`

### Archive Folder Review
The `archive/` folder already has good organization. Consider:
- Keeping as-is (already organized by date/purpose)
- Adding a README.md explaining archive contents

## ✅ Success Criteria

After cleanup:
1. ✅ Root directory has < 10 .md files (only essential docs)
2. ✅ All historical documentation in `docs/history/`
3. ✅ All architecture docs in `docs/architecture/`
4. ✅ All planning docs in `docs/planning/`
5. ✅ Clear organization with README.md in each folder
6. ✅ All cross-references updated
7. ✅ Git history preserved (using `git mv`)

## 📋 Next Steps

1. Review and approve this plan
2. Execute Steps 1-6 (directory creation and moves)
3. Create index README.md files
4. Update cross-references
5. Test that documentation links still work
6. Commit with clear message: "docs: Reorganize documentation into history, architecture, and planning folders"
