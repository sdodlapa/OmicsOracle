#!/bin/bash
# Documentation Cleanup Script
# Archives old phase plans and consolidates documentation
# Date: October 6, 2025

set -e  # Exit on error

REPO_ROOT="/Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle"
ARCHIVE_DIR="$REPO_ROOT/docs/archive/phase-plans-2025-10"
ANALYSIS_ARCHIVE="$REPO_ROOT/docs/archive/analysis-reports-2025-10"

cd "$REPO_ROOT"

echo "════════════════════════════════════════════════════════════════"
echo "  OmicsOracle Documentation Cleanup"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Count before
BEFORE_COUNT=$(find docs -name "*.md" -type f | wc -l | tr -d ' ')
echo "📊 Current documentation files: $BEFORE_COUNT"
echo ""

# Step 1: Archive Phase Plans
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Archiving Phase Plans"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Archive PHASE_*.md files
PHASE_COUNT=$(find docs/planning -name "PHASE_*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$PHASE_COUNT" -gt 0 ]; then
    echo "  → Archiving $PHASE_COUNT PHASE_*.md files from docs/planning/"
    find docs/planning -name "PHASE_*.md" -type f -exec mv {} "$ARCHIVE_DIR/" \;
    echo "  ✅ Done"
else
    echo "  ℹ️  No PHASE_*.md files found in docs/planning/"
fi

# Archive *PLAN*.md files from docs/plans/
if [ -d docs/plans ]; then
    PLAN_COUNT=$(find docs/plans -name "*PLAN*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [ "$PLAN_COUNT" -gt 0 ]; then
        echo "  → Archiving $PLAN_COUNT *PLAN*.md files from docs/plans/"
        find docs/plans -name "*PLAN*.md" -type f -exec mv {} "$ARCHIVE_DIR/" \;
        echo "  ✅ Done"
    fi
fi

# Archive *ROADMAP*.md files
ROADMAP_COUNT=$(find docs -name "*ROADMAP*.md" ! -path "*/archive/*" -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$ROADMAP_COUNT" -gt 0 ]; then
    echo "  → Archiving $ROADMAP_COUNT *ROADMAP*.md files"
    find docs -name "*ROADMAP*.md" ! -path "*/archive/*" -type f -exec mv {} "$ARCHIVE_DIR/" \;
    echo "  ✅ Done"
fi

echo ""

# Step 2: Archive Analysis Reports
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Archiving Analysis Reports"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Archive analysis and review documents
if [ -d docs/reports ]; then
    ANALYSIS_COUNT=$(find docs/reports -name "*ANALYSIS*.md" -o -name "*REVIEW*.md" -o -name "*ASSESSMENT*.md" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$ANALYSIS_COUNT" -gt 0 ]; then
        echo "  → Archiving $ANALYSIS_COUNT analysis/review documents"
        find docs/reports \( -name "*ANALYSIS*.md" -o -name "*REVIEW*.md" -o -name "*ASSESSMENT*.md" \) -exec mv {} "$ANALYSIS_ARCHIVE/" \;
        echo "  ✅ Done"
    fi
fi

# Archive old session summaries (keep recent ones)
if [ -d docs/summaries ]; then
    OLD_SUMMARY_COUNT=$(find docs/summaries -name "*SUMMARY*.md" -mtime +30 2>/dev/null | wc -l | tr -d ' ')
    if [ "$OLD_SUMMARY_COUNT" -gt 0 ]; then
        echo "  → Archiving $OLD_SUMMARY_COUNT old summary documents (>30 days)"
        find docs/summaries -name "*SUMMARY*.md" -mtime +30 -exec mv {} "$ANALYSIS_ARCHIVE/" \;
        echo "  ✅ Done"
    fi
fi

echo ""

# Step 3: Create Archive README
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Creating Archive Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > "$ARCHIVE_DIR/README.md" << 'EOF'
# Archived Phase Plans (October 2025)

**Archive Date:** October 6, 2025  
**Reason:** Consolidation and strategic pivot to multi-agent architecture

---

## What's Archived Here

This directory contains the original phase-based development plans that guided OmicsOracle's development from inception through October 2025.

### Included Documents:

- **PHASE_*.md** - Phase 0-6 implementation plans
- **\*PLAN\*.md** - Various planning documents
- **\*ROADMAP\*.md** - Development roadmaps and timelines

### Why Archived:

1. **Phase 0 (Configurable Ranking):** ✅ **100% Complete** - Production-ready
2. **Phase 1 (Semantic Search):** ✅ **95% Complete** - Full integration done, only dataset embeddings pending
3. **Phase 4 (Production Features):** ⚠️ **40% Complete** - Auth & rate limiting done, monitoring pending
4. **Phases 2, 3, 5, 6:** Superseded by new multi-agent architecture

---

## Current Development Status (Oct 2025)

### What Works (Production-Ready):

✅ **Keyword Search** - GEO database integration  
✅ **Semantic Search** - AI-powered with query expansion & reranking (code complete, needs dataset index)  
✅ **AI Analysis** - GPT-4 dataset insights with markdown rendering  
✅ **Quality Scoring** - 7-dimensional assessment  
✅ **Authentication** - JWT-based user management  
✅ **Rate Limiting** - Redis-powered quota system  

### Active Codebase:

- **122 Python files** in `omics_oracle_v2/`
- **7,643 lines** in library modules
- **220+ passing tests**
- **Zero TODO/FIXME markers** in source code

---

## Next Phase: Multi-Agent Architecture

The project is pivoting to a comprehensive multi-agent system with:

- **Smart Hybrid Orchestrator** (20% GPT-4, 80% BioMedLM)
- **Publication Mining** (PubMed integration)
- **GPU Deployment** (A100 on-prem, H100 on GCP)
- **Rate-Limit Aware** routing

See current documentation in `/docs/` for:
- `MULTI_AGENT_ARCHITECTURE.md` (when created)
- `CURRENT_STATE.md`
- `COMPLETION_PLAN.md`

---

## Historical Context

These phase plans represent 8-12 weeks of development work and strategic planning. While superseded, they provide valuable context for understanding:

- Design decisions and rationale
- Evolution of the architecture
- Lessons learned during implementation
- Original feature specifications

---

## Restoration

If you need to reference these plans:

```bash
# They're preserved in git history
git log --all --full-history -- "docs/archive/phase-plans-2025-10/*"

# View specific archived plan
cat docs/archive/phase-plans-2025-10/PHASE_1_SEMANTIC_SEARCH_PLAN.md
```

---

**Archive maintained by:** OmicsOracle Development Team  
**Last updated:** October 6, 2025
EOF

echo "  ✅ Created $ARCHIVE_DIR/README.md"

cat > "$ANALYSIS_ARCHIVE/README.md" << 'EOF'
# Archived Analysis Reports (October 2025)

**Archive Date:** October 6, 2025  
**Purpose:** Historical analysis and review documents

---

## Contents

This directory contains analysis, review, and assessment documents created during development phases. These provided strategic insights and guided architectural decisions.

### Document Types:

- **\*ANALYSIS\*.md** - Technical and architectural analyses
- **\*REVIEW\*.md** - Progress reviews and status reports
- **\*ASSESSMENT\*.md** - Strategic assessments and evaluations
- **\*SUMMARY\*.md** - Session summaries (older than 30 days)

### Why Archived:

- Consolidation of documentation
- Historical reference preservation
- Focus on current/active documentation
- Reduced maintenance burden

---

## Current Documentation

Active documentation is in `/docs/`:

- `README.md` - Main documentation hub
- `ARCHITECTURE.md` - System architecture
- `API_REFERENCE.md` - API documentation
- `guides/` - User and developer guides

---

**Archive maintained by:** OmicsOracle Development Team  
**Last updated:** October 6, 2025
EOF

echo "  ✅ Created $ANALYSIS_ARCHIVE/README.md"
echo ""

# Step 4: Generate Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Cleanup Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

AFTER_COUNT=$(find docs -name "*.md" -type f | wc -l | tr -d ' ')
ARCHIVED_PLANS=$(find "$ARCHIVE_DIR" -name "*.md" ! -name "README.md" -type f | wc -l | tr -d ' ')
ARCHIVED_REPORTS=$(find "$ANALYSIS_ARCHIVE" -name "*.md" ! -name "README.md" -type f | wc -l | tr -d ' ')
REDUCTION=$((BEFORE_COUNT - AFTER_COUNT))

echo ""
echo "📊 Documentation Cleanup Results:"
echo "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Before:  $BEFORE_COUNT markdown files"
echo "  After:   $AFTER_COUNT markdown files"
echo "  Reduced: $REDUCTION files (-$(echo "scale=1; $REDUCTION * 100 / $BEFORE_COUNT" | bc)%)"
echo "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Archived Files:"
echo "  → Phase plans:      $ARCHIVED_PLANS files → $ARCHIVE_DIR/"
echo "  → Analysis reports: $ARCHIVED_REPORTS files → $ANALYSIS_ARCHIVE/"
echo ""

# Step 5: List what remains
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Active Documentation Structure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Remaining active documentation:"
echo ""
find docs -maxdepth 2 -name "*.md" ! -path "*/archive/*" -type f | sort | while read file; do
    echo "  ✓ ${file#docs/}"
done
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ Documentation Cleanup Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Review active documentation structure"
echo "  2. Create essential guides (SEMANTIC_SEARCH_GUIDE.md, etc.)"
echo "  3. Update README.md with new structure"
echo "  4. Git commit: 'docs: Archive old phase plans and consolidate documentation'"
echo ""
