#!/bin/bash

# OmicsOracle Root Docs Cleanup Script
# Created: October 8, 2025
# Purpose: Move remaining 52 docs from root to appropriate folders

set -e

DOCS_DIR="/Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle/docs"
cd "$DOCS_DIR"

echo "🧹 Starting root docs cleanup..."
echo "📊 Found 52 markdown files in root"
echo ""

# ============================================================================
# 1. PHASE 3 COMPLETION DOCS → archive/phase3-2025-09-to-10/
# ============================================================================
echo "📦 Moving Phase 3 completion docs to archive..."
mkdir -p archive/phase3-2025-09-to-10/completion

mv -v PHASE3_COMPLETION_SUMMARY.md archive/phase3-2025-09-to-10/completion/
mv -v PHASE3_FINAL_VALIDATION_REPORT.md archive/phase3-2025-09-to-10/completion/
mv -v PHASE3_VALIDATION_SUCCESS.md archive/phase3-2025-09-to-10/completion/

echo "✅ Phase 3 docs archived"
echo ""

# ============================================================================
# 2. PHASE 1 DOCS → archive/phase1-2025-09/
# ============================================================================
echo "📦 Moving Phase 1 completion docs to archive..."
mkdir -p archive/phase1-2025-09/completion

mv -v PHASE1_SEMANTIC_SEARCH_COMPLETE.md archive/phase1-2025-09/completion/
mv -v SEMANTIC_SEARCH_API_USAGE.md archive/phase1-2025-09/completion/

echo "✅ Phase 1 docs archived"
echo ""

# ============================================================================
# 3. STATUS/PROGRESS DOCS → archive/phase4-2025-09-to-10/04-completion/
# ============================================================================
echo "📦 Moving status and progress docs to Phase 4 archive..."

mv -v CURRENT_ACCURATE_STATUS.md archive/phase4-2025-09-to-10/04-completion/
mv -v COMPREHENSIVE_PROGRESS_REVIEW.md archive/phase4-2025-09-to-10/04-completion/
mv -v PROGRESS_SUMMARY.md archive/phase4-2025-09-to-10/04-completion/

echo "✅ Status docs archived"
echo ""

# ============================================================================
# 4. FRONTEND PLANNING → phase5-2025-10-to-2025-12/00-overview/
# ============================================================================
echo "📁 Moving frontend planning docs to Phase 5..."
mkdir -p phase5-2025-10-to-2025-12/00-overview

mv -v ALTERNATIVE_FRONTEND_DESIGNS.md phase5-2025-10-to-2025-12/00-overview/
mv -v FRONTEND_PLANNING_SUMMARY.md phase5-2025-10-to-2025-12/00-overview/
mv -v FRONTEND_REDESIGN_ARCHITECTURE.md phase5-2025-10-to-2025-12/00-overview/
mv -v FRONTEND_UI_ANALYSIS.md phase5-2025-10-to-2025-12/00-overview/
mv -v README_FRONTEND_PLANNING.md phase5-2025-10-to-2025-12/00-overview/
mv -v FEATURE_INTEGRATION_PLAN.md phase5-2025-10-to-2025-12/00-overview/
mv -v POST_PHASE4_ROADMAP.md phase5-2025-10-to-2025-12/00-overview/

echo "✅ Frontend planning docs moved to Phase 5"
echo ""

# ============================================================================
# 5. ARCHITECTURE ANALYSIS → archive/phase4-2025-09-to-10/03-decisions/
# ============================================================================
echo "📦 Moving architecture analysis to Phase 4 decisions..."

mv -v ARCHITECTURE_SUITABILITY_VERDICT.md archive/phase4-2025-09-to-10/03-decisions/
mv -v MULTI_AGENT_ARCHITECTURE_ANALYSIS.md archive/phase4-2025-09-to-10/03-decisions/
mv -v STRATEGIC_PIVOT_ASSESSMENT.md archive/phase4-2025-09-to-10/03-decisions/
mv -v UPDATED_STRATEGIC_ASSESSMENT.md archive/phase4-2025-09-to-10/03-decisions/
mv -v OPEN_SOURCE_VS_OPENAI_ANALYSIS.md archive/phase4-2025-09-to-10/03-decisions/

echo "✅ Architecture analysis archived"
echo ""

# ============================================================================
# 6. LLM STRATEGY → archive/phase4-2025-09-to-10/03-decisions/
# ============================================================================
echo "📦 Moving LLM strategy docs to Phase 4 decisions..."

mv -v LLM_NECESSITY_ANALYSIS.md archive/phase4-2025-09-to-10/03-decisions/
mv -v LLM_STRATEGY.md archive/phase4-2025-09-to-10/03-decisions/

echo "✅ LLM strategy docs archived"
echo ""

# ============================================================================
# 7. RATE LIMITING DOCS → current-2025-10/features/
# ============================================================================
echo "📁 Moving rate limiting docs to current features..."

mv -v RATE_LIMITING.md current-2025-10/features/
mv -v RATE_LIMITING_ANALYSIS.md current-2025-10/features/
mv -v RATE_LIMITING_ADDENDUM.md current-2025-10/features/

echo "✅ Rate limiting docs moved to current features"
echo ""

# ============================================================================
# 8. PUBLICATION MINING → current-2025-10/features/
# ============================================================================
echo "📁 Moving publication mining docs to current features..."

mv -v PUBLICATION_MINING_EXAMPLE.md current-2025-10/features/
mv -v PUBLICATION_MINING_INDEX.md current-2025-10/features/

echo "✅ Publication mining docs moved to current features"
echo ""

# ============================================================================
# 9. SYSTEM AUDIT DOCS → archive/phase4-2025-09-to-10/02-planning/
# ============================================================================
echo "📦 Moving system audit docs to Phase 4 planning..."

mv -v SYSTEM_AUDIT_PHASE1.md archive/phase4-2025-09-to-10/02-planning/
mv -v SYSTEM_AUDIT_PHASE2.md archive/phase4-2025-09-to-10/02-planning/
mv -v SYSTEM_AUDIT_PHASE3.md archive/phase4-2025-09-to-10/02-planning/

echo "✅ System audit docs archived"
echo ""

# ============================================================================
# 10. DASHBOARD & DISPLAY → current-2025-10/features/
# ============================================================================
echo "📁 Moving dashboard and display docs to current features..."

mv -v DASHBOARD_DISPLAY_GUIDE.md current-2025-10/features/
mv -v INSTITUTIONAL_ACCESS_DEMO.md current-2025-10/features/
mv -v SEARCH_VS_DASHBOARD_COMPARISON.md current-2025-10/features/

echo "✅ Dashboard docs moved to current features"
echo ""

# ============================================================================
# 11. DEVELOPER GUIDES → current-2025-10/guides/
# ============================================================================
echo "📁 Moving developer guides to current guides folder..."
mkdir -p current-2025-10/guides

mv -v DEVELOPER_GUIDE.md current-2025-10/guides/
mv -v DEPLOYMENT_GUIDE.md current-2025-10/guides/
mv -v DEPLOYMENT_V2_GUIDE.md current-2025-10/guides/
mv -v STARTUP_GUIDE.md current-2025-10/guides/
mv -v WEB_INTERFACE_DEMO_GUIDE.md current-2025-10/guides/

echo "✅ Developer guides moved"
echo ""

# ============================================================================
# 12. TESTING DOCS → current-2025-10/testing/
# ============================================================================
echo "📁 Moving testing documentation to current testing folder..."
mkdir -p current-2025-10/testing

mv -v TEST_ORGANIZATION.md current-2025-10/testing/
mv -v TEST_TEMPLATES.md current-2025-10/testing/
mv -v TESTING_HIERARCHY.md current-2025-10/testing/
mv -v TESTING_RESULTS_ANALYSIS.md current-2025-10/testing/

echo "✅ Testing docs moved"
echo ""

# ============================================================================
# 13. CODE QUALITY → current-2025-10/guides/
# ============================================================================
echo "📁 Moving code quality docs to guides..."

mv -v CODE_QUALITY_GUIDE.md current-2025-10/guides/
mv -v ASCII_ENFORCEMENT_GUIDE.md current-2025-10/guides/

echo "✅ Code quality docs moved"
echo ""

# ============================================================================
# 14. PACKAGE & SYSTEM DOCS → current-2025-10/architecture/
# ============================================================================
echo "📁 Moving package and system docs to architecture..."

mv -v PACKAGE_STRUCTURE.md current-2025-10/architecture/
mv -v INDEX.md current-2025-10/architecture/
mv -v debugging_sequence_diagram.md current-2025-10/architecture/
mv -v SYSTEM_STATUS_WARNINGS_EXPLAINED.md current-2025-10/architecture/

echo "✅ Package and system docs moved"
echo ""

# ============================================================================
# 15. DELETE TEMPORARY PLANNING DOCS
# ============================================================================
echo "🗑️  Removing temporary planning documents..."

rm -v PHASE5_CLEANUP_AND_REORGANIZATION.md
rm -v PHASE5_CLEANUP_DATED.md

echo "✅ Temporary planning docs removed"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ ROOT DOCS CLEANUP COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Summary:"
echo "   • Phase 3 docs → archive/phase3-2025-09-to-10/"
echo "   • Phase 1 docs → archive/phase1-2025-09/"
echo "   • Status docs → archive/phase4-2025-09-to-10/04-completion/"
echo "   • Frontend planning → phase5-2025-10-to-2025-12/00-overview/"
echo "   • Architecture analysis → archive/phase4-2025-09-to-10/03-decisions/"
echo "   • LLM strategy → archive/phase4-2025-09-to-10/03-decisions/"
echo "   • Rate limiting → current-2025-10/features/"
echo "   • Publication mining → current-2025-10/features/"
echo "   • System audits → archive/phase4-2025-09-to-10/02-planning/"
echo "   • Dashboard docs → current-2025-10/features/"
echo "   • Developer guides → current-2025-10/guides/"
echo "   • Testing docs → current-2025-10/testing/"
echo "   • Code quality → current-2025-10/guides/"
echo "   • Package docs → current-2025-10/architecture/"
echo "   • Temporary docs → DELETED"
echo ""
echo "📁 New folder structure:"
echo "   current-2025-10/"
echo "   ├── api/"
echo "   ├── architecture/"
echo "   ├── features/"
echo "   ├── guides/"
echo "   ├── integration/"
echo "   └── testing/"
echo ""
echo "🎯 Root docs folder should now only contain:"
echo "   • README.md (main index)"
echo "   • REORGANIZATION_SUMMARY.md (record of cleanup)"
echo ""
echo "Next steps:"
echo "1. Review moved files: ls -R current-2025-10/ phase5-2025-10-to-2025-12/ archive/"
echo "2. Verify root is clean: ls docs/*.md"
echo "3. Commit changes: git add docs/ && git commit -m 'docs: Clean up root folder'"
echo ""
