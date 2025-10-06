#!/bin/bash

# OmicsOracle Root Documentation Organization
# Move all .md files from root to appropriate docs/ locations

cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle

echo "════════════════════════════════════════════════════════════════"
echo "  OmicsOracle Root Documentation Organization"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Create necessary directories
echo "📁 Creating organization directories..."
mkdir -p docs/reports
mkdir -p docs/planning
mkdir -p docs/summaries
mkdir -p docs/archive/old-root-docs-2025-10

# Count files before
BEFORE=$(ls -1 *.md 2>/dev/null | wc -l | tr -d ' ')
echo "�� Root .md files before: $BEFORE"
echo ""

echo "━━━ Moving Architecture & System Docs ━━━"
# Architecture already in docs/, move if in root
if [ -f "ARCHITECTURE.md" ]; then
    echo "  → ARCHITECTURE.md already in docs/, archiving root copy"
    mv ARCHITECTURE.md docs/archive/old-root-docs-2025-10/
fi

echo "━━━ Moving Planning & Status Docs ━━━"
# Planning and status documents → docs/planning/
[ -f "COMPLETION_PLAN.md" ] && mv COMPLETION_PLAN.md docs/planning/ && echo "  ✅ COMPLETION_PLAN.md → docs/planning/"
[ -f "IMPLEMENTATION_ROADMAP.md" ] && mv IMPLEMENTATION_ROADMAP.md docs/planning/ && echo "  ✅ IMPLEMENTATION_ROADMAP.md → docs/planning/"
[ -f "PHASE1_STATUS.md" ] && mv PHASE1_STATUS.md docs/planning/ && echo "  ✅ PHASE1_STATUS.md → docs/planning/"

echo ""
echo "━━━ Moving Analysis & Report Docs ━━━"
# Reports and analyses → docs/reports/
[ -f "CODE_AUDIT_REPORT.md" ] && mv CODE_AUDIT_REPORT.md docs/reports/ && echo "  ✅ CODE_AUDIT_REPORT.md → docs/reports/"
[ -f "DOCUMENTATION_CLEANUP_SUMMARY.md" ] && mv DOCUMENTATION_CLEANUP_SUMMARY.md docs/reports/ && echo "  ✅ DOCUMENTATION_CLEANUP_SUMMARY.md → docs/reports/"

echo ""
echo "━━━ Moving Quick Start & Testing Guides ━━━"
# Quick start already exists in docs/, archive duplicates
[ -f "QUICK_START.md" ] && mv QUICK_START.md docs/archive/old-root-docs-2025-10/ && echo "  ✅ QUICK_START.md → archive (duplicate)"
[ -f "QUICK_TEST_GUIDE.md" ] && mv QUICK_TEST_GUIDE.md docs/testing/ && echo "  ✅ QUICK_TEST_GUIDE.md → docs/testing/"
[ -f "QUICK_TESTING_GUIDE.md" ] && mv QUICK_TESTING_GUIDE.md docs/testing/ && echo "  ✅ QUICK_TESTING_GUIDE.md → docs/testing/"

echo ""
echo "━━━ Moving Session Summaries ━━━"
# Session summaries → docs/summaries/
[ -f "READY_FOR_TESTING.md" ] && mv READY_FOR_TESTING.md docs/summaries/ && echo "  ✅ READY_FOR_TESTING.md → docs/summaries/"
[ -f "READY_TO_USE.md" ] && mv READY_TO_USE.md docs/summaries/ && echo "  ✅ READY_TO_USE.md → docs/summaries/"
[ -f "TESTING_PROGRESS.md" ] && mv TESTING_PROGRESS.md docs/summaries/ && echo "  ✅ TESTING_PROGRESS.md → docs/summaries/"
[ -f "UNDERSTANDING_TEST_RESULTS.md" ] && mv UNDERSTANDING_TEST_RESULTS.md docs/summaries/ && echo "  ✅ UNDERSTANDING_TEST_RESULTS.md → docs/summaries/"
[ -f "WHY_THESE_ARE_NOT_BUGS.md" ] && mv WHY_THESE_ARE_NOT_BUGS.md docs/summaries/ && echo "  ✅ WHY_THESE_ARE_NOT_BUGS.md → docs/summaries/"

echo ""
echo "━━━ Archiving Old Reorganization Docs ━━━"
# Old reorganization docs → archive
[ -f "CODEBASE_REORGANIZATION.md" ] && mv CODEBASE_REORGANIZATION.md docs/archive/old-root-docs-2025-10/ && echo "  ✅ CODEBASE_REORGANIZATION.md → archive"
[ -f "REORGANIZATION_COMPLETE.md" ] && mv REORGANIZATION_COMPLETE.md docs/archive/old-root-docs-2025-10/ && echo "  ✅ REORGANIZATION_COMPLETE.md → archive"

echo ""
echo "━━━ Creating Archive README ━━━"
cat > docs/archive/old-root-docs-2025-10/README.md << 'ARCHIVE_EOF'
# Old Root Documentation (October 2025)

This directory contains documentation files that were previously in the repository root.
These files were moved during the October 2025 documentation cleanup.

## Why These Were Moved

Root directory should only contain:
- README.md - Main project README
- README_NEW.md - Updated README (pending replacement)
- Essential config files (pyproject.toml, etc.)

All other documentation belongs in organized `docs/` subdirectories.

## Files Archived Here

### Duplicate Files
- `ARCHITECTURE.md` - Duplicate of docs/ARCHITECTURE.md
- `QUICK_START.md` - Duplicate of docs/QUICK_START.md

### Old Reorganization Docs
- `CODEBASE_REORGANIZATION.md` - October 2025 reorganization summary
- `REORGANIZATION_COMPLETE.md` - Reorganization completion notice

These represent historical reorganization efforts and are kept for reference.

## Reference

For current documentation, see:
- Architecture: `docs/SYSTEM_ARCHITECTURE.md`
- Quick Start: `docs/STARTUP_GUIDE.md`
- Current State: Root `CURRENT_STATE.md`
- Planning: `docs/planning/`
- Reports: `docs/reports/`
- Summaries: `docs/summaries/`

---
**Archived:** October 6, 2025
ARCHIVE_EOF

echo "  ✅ Created archive README"

echo ""
echo "━━━ Summary ━━━"
AFTER=$(ls -1 *.md 2>/dev/null | wc -l | tr -d ' ')
MOVED=$((BEFORE - AFTER))

echo "📊 Before:  $BEFORE .md files in root"
echo "📊 After:   $AFTER .md files in root"
echo "📊 Moved:   $MOVED files"
echo ""

echo "📁 Files Organized By Category:"
echo "  → Planning:   $(ls -1 docs/planning/*.md 2>/dev/null | wc -l | tr -d ' ') files"
echo "  → Reports:    $(ls -1 docs/reports/*.md 2>/dev/null | wc -l | tr -d ' ') files"
echo "  → Summaries:  $(ls -1 docs/summaries/*.md 2>/dev/null | wc -l | tr -d ' ') files"
echo "  → Testing:    $(ls -1 docs/testing/*.md 2>/dev/null | wc -l | tr -d ' ') files"
echo "  → Archived:   $(ls -1 docs/archive/old-root-docs-2025-10/*.md 2>/dev/null | wc -l | tr -d ' ') files"
echo ""

echo "📋 Remaining in root:"
ls -1 *.md 2>/dev/null | sed 's/^/  - /'

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Root Documentation Organization Complete!"
echo "════════════════════════════════════════════════════════════════"
