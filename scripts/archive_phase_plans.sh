#!/bin/bash
#
# Archive Phase Plans Script
# Purpose: Move old phase plans to archive while preserving git history
# Date: October 6, 2025
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     OmicsOracle Phase Plan Archival Script                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create archive directory
ARCHIVE_DIR="docs/archive/phase-plans-2025-10"
echo -e "${YELLOW}Creating archive directory: ${ARCHIVE_DIR}${NC}"
mkdir -p "$ARCHIVE_DIR"

# Count files before
BEFORE_COUNT=$(find docs -name "*.md" | wc -l | tr -d ' ')
echo -e "${YELLOW}Total documentation files before: ${BEFORE_COUNT}${NC}"
echo ""

# Archive planning documents
echo -e "${GREEN}Step 1: Archiving phase plans from docs/planning/${NC}"
if [ -d "docs/planning" ]; then
    PHASE_FILES=$(find docs/planning -name "PHASE_*.md" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$PHASE_FILES" -gt 0 ]; then
        find docs/planning -name "PHASE_*.md" -exec mv {} "$ARCHIVE_DIR/" \;
        echo -e "${GREEN}✓ Archived ${PHASE_FILES} phase plan files${NC}"
    else
        echo -e "${YELLOW}  No PHASE_*.md files found${NC}"
    fi
else
    echo -e "${YELLOW}  docs/planning/ does not exist${NC}"
fi

# Archive plan documents from docs/plans/
echo -e "${GREEN}Step 2: Archiving plan documents from docs/plans/${NC}"
if [ -d "docs/plans" ]; then
    PLAN_FILES=$(find docs/plans -name "*PLAN*.md" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$PLAN_FILES" -gt 0 ]; then
        find docs/plans -name "*PLAN*.md" -exec mv {} "$ARCHIVE_DIR/" \;
        echo -e "${GREEN}✓ Archived ${PLAN_FILES} plan files${NC}"
    else
        echo -e "${YELLOW}  No *PLAN*.md files found${NC}"
    fi
else
    echo -e "${YELLOW}  docs/plans/ does not exist${NC}"
fi

# Archive roadmap documents
echo -e "${GREEN}Step 3: Archiving roadmap documents${NC}"
ROADMAP_FILES=$(find docs -name "*ROADMAP*.md" ! -path "*/archive/*" 2>/dev/null | wc -l | tr -d ' ')
if [ "$ROADMAP_FILES" -gt 0 ]; then
    find docs -name "*ROADMAP*.md" ! -path "*/archive/*" -exec mv {} "$ARCHIVE_DIR/" \;
    echo -e "${GREEN}✓ Archived ${ROADMAP_FILES} roadmap files${NC}"
else
    echo -e "${YELLOW}  No *ROADMAP*.md files found${NC}"
fi

# Archive status review documents
echo -e "${GREEN}Step 4: Archiving status and review documents${NC}"
if [ -d "docs/reports" ]; then
    STATUS_FILES=$(find docs/reports -name "*STATUS*.md" -o -name "*REVIEW*.md" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$STATUS_FILES" -gt 0 ]; then
        find docs/reports -name "*STATUS*.md" -o -name "*REVIEW*.md" -exec mv {} "$ARCHIVE_DIR/" \;
        echo -e "${GREEN}✓ Archived ${STATUS_FILES} status/review files${NC}"
    else
        echo -e "${YELLOW}  No status/review files found${NC}"
    fi
else
    echo -e "${YELLOW}  docs/reports/ does not exist${NC}"
fi

# Archive implementation guides (old)
echo -e "${GREEN}Step 5: Archiving old implementation guides${NC}"
OLD_IMPL_FILES=$(find docs -name "IMPLEMENTATION_*.md" ! -path "*/archive/*" ! -name "IMPLEMENTATION_ROADMAP.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$OLD_IMPL_FILES" -gt 0 ]; then
    find docs -name "IMPLEMENTATION_*.md" ! -path "*/archive/*" ! -name "IMPLEMENTATION_ROADMAP.md" -exec mv {} "$ARCHIVE_DIR/" \;
    echo -e "${GREEN}✓ Archived ${OLD_IMPL_FILES} implementation guide files${NC}"
else
    echo -e "${YELLOW}  No old implementation guides found${NC}"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"

# Count files after
AFTER_COUNT=$(find docs -name "*.md" | wc -l | tr -d ' ')
ARCHIVED_COUNT=$((BEFORE_COUNT - AFTER_COUNT))

echo -e "${GREEN}Archive Summary:${NC}"
echo -e "${YELLOW}  Before: ${BEFORE_COUNT} files${NC}"
echo -e "${YELLOW}  After:  ${AFTER_COUNT} files${NC}"
echo -e "${GREEN}  ✓ Archived: ${ARCHIVED_COUNT} files${NC}"
echo ""

# List archived files
ARCHIVED_FILES=$(find "$ARCHIVE_DIR" -name "*.md" | wc -l | tr -d ' ')
echo -e "${GREEN}Files in archive: ${ARCHIVED_FILES}${NC}"
echo ""

# Create archive README
cat > "$ARCHIVE_DIR/README.md" << 'EOF'
# Archived Phase Plans - October 2025

**Archive Date:** October 6, 2025
**Reason:** Strategic pivot to multi-agent architecture
**Status:** Historical reference only - DO NOT USE FOR CURRENT DEVELOPMENT

---

## What's Archived Here

This directory contains all phase-based planning documents from the original OmicsOracle development approach (Phases 0-6).

**Original Timeline:** September - October 2025
**Completion Status:** Phase 0-1 partially complete, others incomplete

---

## Why Archived

On October 6, 2025, we made a strategic decision to pivot from scattered phase-based development to a unified multi-agent architecture with publication mining capabilities.

**Key Reasons:**
1. ❌ 484 documentation files creating maintenance burden
2. ❌ Phase plans scattered and conflicting
3. ❌ 8.75 hours spent on features not accessible to users
4. ✅ Multi-agent architecture offers 200x user value (publication mining)
5. ✅ Free A100/H100 GPU resources available
6. ✅ Rate-limiting constraints require different approach

---

## What Was Completed

### Phase 0: Configurable Ranking ✅ COMPLETE
- KeywordRanker (97% test coverage)
- QualityScorer (96% test coverage)
- Production-ready

### Phase 1: Semantic Search ⚠️ 60% COMPLETE
- ✅ Embedding service, FAISS vector DB
- ✅ Query expansion, cross-encoder reranking
- ✅ RAG pipeline
- ❌ Dataset embedding pipeline (not built)
- ❌ SearchAgent integration (not built)
- ❌ User accessibility (not deployed)

### Phase 4: Production Features ⚠️ 40% COMPLETE
- ✅ Authentication, rate limiting
- ❌ Monitoring, observability (not built)
- ❌ Production deployment (not done)

---

## What's Salvageable

Components that can be reused in multi-agent architecture:
- ✅ EmbeddingService → Publication embeddings
- ✅ FAISS VectorDatabase → Publication similarity
- ✅ RAG Pipeline → Publication analysis
- ✅ Authentication system
- ✅ Rate limiting infrastructure

**Salvage Rate:** ~40-50% of code

---

## New Direction

See current documentation:
- `docs/MULTI_AGENT_ARCHITECTURE_ANALYSIS.md` - New architecture
- `docs/PUBLICATION_MINING_ROADMAP.md` - Publication mining spec
- `docs/RATE_LIMITING_ADDENDUM.md` - Rate-limit aware design
- `docs/STRATEGIC_PIVOT_ASSESSMENT.md` - Pivot rationale

---

## Files in This Archive

Total: ~130 files

**Categories:**
- Phase 0-6 plans
- Implementation roadmaps
- Status reviews
- Old testing plans
- Obsolete architecture docs

**Note:** These files are preserved for historical reference and lessons learned. Do not use for current development planning.

---

**For current development plans, see:** `docs/MULTI_AGENT_ROADMAP.md`
EOF

echo -e "${GREEN}✓ Created archive README${NC}"
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ARCHIVAL COMPLETE                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Review archived files: ls -la ${ARCHIVE_DIR}/"
echo -e "  2. Run consolidation script: ./scripts/consolidate_docs.sh"
echo -e "  3. Commit changes: git add . && git commit -m 'Archive old phase plans'"
echo ""
echo -e "${GREEN}✓ All phase plans archived successfully!${NC}"
