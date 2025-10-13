# Repository Cleanup Plan V2
**Date:** October 13, 2025
**Purpose:** Follow existing date-based naming patterns to organize root documents

## 📊 Existing Organization Pattern

The docs folder already follows a clear date-based pattern:
- `docs/current-2025-10/` - Current October 2025 work
- `docs/history/week_3/` - Historical week 3 work
- `docs/phase5-2025-10-to-2025-12/` - Phase 5 planning
- `docs/phase5-review-2025-10-08/` - Phase 5 review
- `docs/phase6-consolidation/` - Phase 6 work
- `archive/docs-2025-10-12-historical/` - Archived docs with date

## 🎯 Root Documents to Organize (30+ files)

### Group 1: Phase 2 & Phase 3 Historical Work (Sept-Oct 2025)
**Move to:** `docs/history/phase2-phase3-2025-09-10/`

Phase 2 documents:
- `PHASE2B_COMPLETE.md`
- `PHASE2B_FLOW_REORGANIZATION.md`
- `PHASE2B_PHASE3_SUMMARY.md`
- `PHASE2B_PROGRESS.md`
- `PHASE2B_STEP8_COMPLETE.md`
- `PHASE2B_VALIDATION_REPORT.md`
- `PHASE2_CLEANUP_SUMMARY.md`
- `MIGRATION_GUIDE_PHASE2B.md`

Phase 3 documents:
- `PHASE3_NEXT_STEPS.md`
- `PHASE3_TEST_VALIDATION_REPORT.md`

Phase 1 (earlier):
- `PHASE1_COMPLETE.md`
- `PHASE1_FINAL_STATUS.md`

### Group 2: Week 3 Performance Optimization (Oct 2025)
**Move to:** `docs/history/week_3/` (folder exists)

Week 3 documents (Days 16-18):
- `WEEK3_COMPLETE_SUMMARY.md`
- `WEEK3_DAY1_CACHE_OPTIMIZATION_PLAN.md`
- `WEEK3_DAY2_GEO_PARALLELIZATION_PLAN.md`
- `WEEK3_DAYS1-2_COMPLETION_SUMMARY.md`

Note: Already has WEEK3_DAY14_HANDOFF.md and WEEK3_DAY15_COMPLETE.md

### Group 3: Architecture & Flow Analysis (Oct 2025)
**Move to:** `docs/architecture-review-2025-10/`

Architecture documents:
- `ARCHITECTURE_ANALYSIS_REPORT.md`
- `ARCHITECTURE_FLOW_DIAGRAM.md`
- `MANUAL_ARCHITECTURE_VERIFICATION.md`
- `COMPREHENSIVE_CODEBASE_REVIEW.md`
- `LAYER_4_AND_6_EXPLAINED.md`

Flow analysis:
- `ACTUAL_FLOW_ANALYSIS.md`
- `COMPLETE_FLOW_ANALYSIS.md`
- `END_TO_END_FLOW_ANALYSIS.md`
- `FLOW_DIAGRAM.md`
- `FLOW_FILE_MAPPING.md`
- `README_FLOW_ANALYSIS.md`

### Group 4: Cleanup Planning (Oct 2025)
**Move to:** `docs/cleanup-2025-10/`

Cleanup documents:
- `CLEANUP_PLAN_DETAILED.md`
- `CLEANUP_SUMMARY.md`
- `CODE_CLEANUP_PLAN.md`
- `QUICK_CLEANUP_ACTIONS.md`
- `STAGE_BY_STAGE_CLEANUP_PLAN.md`

Stage reports:
- `STAGE_1_TESTING_REPORT.md`
- `STAGE_2_ANALYSIS.md`

## 📁 Execution Plan

### Step 1: Create New Dated Folders
```bash
mkdir -p docs/history/phase2-phase3-2025-09-10
mkdir -p docs/architecture-review-2025-10
mkdir -p docs/cleanup-2025-10
```

### Step 2: Move Phase 2/3 Documents (Historical)
```bash
# Move to historical phases folder
git mv PHASE1_COMPLETE.md docs/history/phase2-phase3-2025-09-10/
git mv PHASE1_FINAL_STATUS.md docs/history/phase2-phase3-2025-09-10/
git mv PHASE2B_COMPLETE.md docs/history/phase2-phase3-2025-09-10/
git mv PHASE2B_FLOW_REORGANIZATION.md docs/history/phase2-phase3-2025-09-10/
git mv PHASE2B_PHASE3_SUMMARY.md docs/history/phase2-phase3-2025-09-10/
git mv PHASE2B_PROGRESS.md docs/history/phase2-phase3-2025-09-10/
git mv PHASE2B_STEP8_COMPLETE.md docs/history/phase2-phase3-2025-09-10/
git mv PHASE2B_VALIDATION_REPORT.md docs/history/phase2-phase3-2025-09-10/
git mv PHASE2_CLEANUP_SUMMARY.md docs/history/phase2-phase3-2025-09-10/
git mv MIGRATION_GUIDE_PHASE2B.md docs/history/phase2-phase3-2025-09-10/
git mv PHASE3_NEXT_STEPS.md docs/history/phase2-phase3-2025-09-10/
git mv PHASE3_TEST_VALIDATION_REPORT.md docs/history/phase2-phase3-2025-09-10/
```

### Step 3: Move Week 3 Documents (to existing folder)
```bash
# Move to existing week_3 folder
git mv WEEK3_COMPLETE_SUMMARY.md docs/history/week_3/
git mv WEEK3_DAY1_CACHE_OPTIMIZATION_PLAN.md docs/history/week_3/
git mv WEEK3_DAY2_GEO_PARALLELIZATION_PLAN.md docs/history/week_3/
git mv WEEK3_DAYS1-2_COMPLETION_SUMMARY.md docs/history/week_3/
```

### Step 4: Move Architecture & Flow Analysis
```bash
# Move to architecture review folder
git mv ARCHITECTURE_ANALYSIS_REPORT.md docs/architecture-review-2025-10/
git mv ARCHITECTURE_FLOW_DIAGRAM.md docs/architecture-review-2025-10/
git mv MANUAL_ARCHITECTURE_VERIFICATION.md docs/architecture-review-2025-10/
git mv COMPREHENSIVE_CODEBASE_REVIEW.md docs/architecture-review-2025-10/
git mv LAYER_4_AND_6_EXPLAINED.md docs/architecture-review-2025-10/
git mv ACTUAL_FLOW_ANALYSIS.md docs/architecture-review-2025-10/
git mv COMPLETE_FLOW_ANALYSIS.md docs/architecture-review-2025-10/
git mv END_TO_END_FLOW_ANALYSIS.md docs/architecture-review-2025-10/
git mv FLOW_DIAGRAM.md docs/architecture-review-2025-10/
git mv FLOW_FILE_MAPPING.md docs/architecture-review-2025-10/
git mv README_FLOW_ANALYSIS.md docs/architecture-review-2025-10/
```

### Step 5: Move Cleanup Planning Documents
```bash
# Move to cleanup folder
git mv CLEANUP_PLAN_DETAILED.md docs/cleanup-2025-10/
git mv CLEANUP_SUMMARY.md docs/cleanup-2025-10/
git mv CODE_CLEANUP_PLAN.md docs/cleanup-2025-10/
git mv QUICK_CLEANUP_ACTIONS.md docs/cleanup-2025-10/
git mv STAGE_BY_STAGE_CLEANUP_PLAN.md docs/cleanup-2025-10/
git mv STAGE_1_TESTING_REPORT.md docs/cleanup-2025-10/
git mv STAGE_2_ANALYSIS.md docs/cleanup-2025-10/
```

### Step 6: Move This Cleanup Plan
```bash
# Move cleanup plans themselves to the cleanup folder
git mv REPO_CLEANUP_PLAN.md docs/cleanup-2025-10/
git mv REPO_CLEANUP_PLAN_V2.md docs/cleanup-2025-10/
```

### Step 7: Create README files
```bash
# Create index files in each new folder
```

## 📝 Files to Keep in Root

### Essential Documentation (Keep)
- `README.md` - Main project documentation ✅
- `CURRENT_STATUS.md` - Active status tracking ✅
- `NEXT_STEPS.md` - Active planning ✅

### Configuration Files (Keep)
All config files stay in root as expected by tools.

## 📊 Result Summary

### Before Cleanup
- Root: 30+ .md files
- Hard to find specific documentation
- Mixed historical and current docs

### After Cleanup
- Root: 3 .md files (README, CURRENT_STATUS, NEXT_STEPS)
- Clear date-based organization
- Easy to find historical work by date/phase
- Follows existing docs folder patterns

## 🎯 Folder Structure After Cleanup

```
OmicsOracle/
├── README.md                          ✅ Keep
├── CURRENT_STATUS.md                  ✅ Keep
├── NEXT_STEPS.md                      ✅ Keep
└── docs/
    ├── current-2025-10/               ✅ Existing (Week 4 work)
    ├── history/
    │   ├── phase2-phase3-2025-09-10/  🆕 NEW (12 phase docs)
    │   └── week_3/                    ✅ Existing + 4 new docs
    ├── architecture-review-2025-10/   🆕 NEW (11 analysis docs)
    ├── cleanup-2025-10/               🆕 NEW (9 cleanup docs)
    ├── phase5-2025-10-to-2025-12/     ✅ Existing
    ├── phase5-review-2025-10-08/      ✅ Existing
    └── phase6-consolidation/          ✅ Existing
```

## ✅ Success Criteria

1. ✅ Root has only 3 .md files (essential docs)
2. ✅ Historical work organized by date/phase
3. ✅ Follows existing docs folder patterns
4. ✅ Date-based naming: `*-2025-10/` format
5. ✅ Git history preserved (using `git mv`)
6. ✅ All moves in single commit

## 🚀 Ready to Execute

All 30+ root documents will be organized into 3 new dated folders:
- `docs/history/phase2-phase3-2025-09-10/` - 12 files
- `docs/architecture-review-2025-10/` - 11 files
- `docs/cleanup-2025-10/` - 9 files

Plus 4 files to existing `docs/history/week_3/`

Total: 36 files moved, 3 files kept in root.
