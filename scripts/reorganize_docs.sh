#!/bin/bash

# OmicsOracle Documentation Reorganization Script
# Date: October 8, 2025
# Purpose: Reorganize docs with date-based folder structure

set -e  # Exit on error

echo "🚀 Starting OmicsOracle Documentation Reorganization..."
echo "Date: $(date)"
echo ""

# Navigate to docs directory
cd "$(dirname "$0")/docs"

# Backup current state
echo "📦 Creating backup..."
BACKUP_DIR="../docs-backup-$(date +%Y%m%d-%H%M%S)"
cp -r . "$BACKUP_DIR"
echo "✅ Backup created at: $BACKUP_DIR"
echo ""

# Step 1: Create new folder structure
echo "📁 Creating new folder structure..."

# Current documentation
mkdir -p current-2025-10/{architecture,api,features,integration}

# Phase 5 with sprints
mkdir -p phase5-2025-10-to-2025-12/00-overview
mkdir -p phase5-2025-10-to-2025-12/01-sprint1-2025-10-08-to-10-22
mkdir -p phase5-2025-10-to-2025-12/02-sprint2-2025-10-23-to-11-06
mkdir -p phase5-2025-10-to-2025-12/03-sprint3-2025-11-07-to-11-21
mkdir -p phase5-2025-10-to-2025-12/04-sprint4-2025-11-22-to-12-06

# Archive structure
mkdir -p archive/phase4-2025-09-to-10/00-overview
mkdir -p archive/phase4-2025-09-to-10/01-daily-progress/day1-2025-10-01
mkdir -p archive/phase4-2025-09-to-10/01-daily-progress/day2-2025-10-02
mkdir -p archive/phase4-2025-09-to-10/01-daily-progress/day3-2025-10-03
mkdir -p archive/phase4-2025-09-to-10/01-daily-progress/day4-2025-10-04
mkdir -p archive/phase4-2025-09-to-10/01-daily-progress/day6-2025-10-05
mkdir -p archive/phase4-2025-09-to-10/01-daily-progress/day7-2025-10-06
mkdir -p archive/phase4-2025-09-to-10/01-daily-progress/day8-2025-10-07
mkdir -p archive/phase4-2025-09-to-10/01-daily-progress/days9-10-2025-10-08
mkdir -p archive/phase4-2025-09-to-10/02-planning
mkdir -p archive/phase4-2025-09-to-10/03-decisions
mkdir -p archive/phase4-2025-09-to-10/04-completion
mkdir -p archive/sessions-2025-08-to-10
mkdir -p archive/tasks-2025-09-to-10

echo "✅ Folder structure created"
echo ""

# Step 2: Move Phase 4 documents
echo "📦 Archiving Phase 4 documents..."

# Overview
[ -f "PHASE4_COMPLETE.md" ] && mv PHASE4_COMPLETE.md archive/phase4-2025-09-to-10/00-overview/
[ -f "PHASE4_ARCHITECTURAL_DECISION.md" ] && mv PHASE4_ARCHITECTURAL_DECISION.md archive/phase4-2025-09-to-10/00-overview/

# Daily progress
[ -f "PHASE4_DAY1_AUTH_SUCCESS.md" ] && mv PHASE4_DAY1_AUTH_SUCCESS.md archive/phase4-2025-09-to-10/01-daily-progress/day1-2025-10-01/

[ -f "PHASE4_DAY2_DISCOVERY.md" ] && mv PHASE4_DAY2_DISCOVERY.md archive/phase4-2025-09-to-10/01-daily-progress/day2-2025-10-02/
[ -f "PHASE4_DAY2_SUCCESS.md" ] && mv PHASE4_DAY2_SUCCESS.md archive/phase4-2025-09-to-10/01-daily-progress/day2-2025-10-02/

[ -f "PHASE4_DAY3_COMPLETE.md" ] && mv PHASE4_DAY3_COMPLETE.md archive/phase4-2025-09-to-10/01-daily-progress/day3-2025-10-03/

[ -f "PHASE4_DAY4_COMPLETE.md" ] && mv PHASE4_DAY4_COMPLETE.md archive/phase4-2025-09-to-10/01-daily-progress/day4-2025-10-04/

[ -f "PHASE4_DAY6_PLAN.md" ] && mv PHASE4_DAY6_PLAN.md archive/phase4-2025-09-to-10/01-daily-progress/day6-2025-10-05/
[ -f "PHASE4_DAY6_COMPLETE.md" ] && mv PHASE4_DAY6_COMPLETE.md archive/phase4-2025-09-to-10/01-daily-progress/day6-2025-10-05/

[ -f "PHASE4_DAY7_PLAN.md" ] && mv PHASE4_DAY7_PLAN.md archive/phase4-2025-09-to-10/01-daily-progress/day7-2025-10-06/
[ -f "PHASE4_DAY7_COMPLETE.md" ] && mv PHASE4_DAY7_COMPLETE.md archive/phase4-2025-09-to-10/01-daily-progress/day7-2025-10-06/

[ -f "PHASE4_DAY8_PROGRESS.md" ] && mv PHASE4_DAY8_PROGRESS.md archive/phase4-2025-09-to-10/01-daily-progress/day8-2025-10-07/
[ -f "PHASE4_DAY8_BUG_FIX.md" ] && mv PHASE4_DAY8_BUG_FIX.md archive/phase4-2025-09-to-10/01-daily-progress/day8-2025-10-07/
[ -f "PHASE4_DAY8_BROWSER_TESTING.md" ] && mv PHASE4_DAY8_BROWSER_TESTING.md archive/phase4-2025-09-to-10/01-daily-progress/day8-2025-10-07/
[ -f "PHASE4_DAY8_TEST_RESULTS.md" ] && mv PHASE4_DAY8_TEST_RESULTS.md archive/phase4-2025-09-to-10/01-daily-progress/day8-2025-10-07/
[ -f "PHASE4_DAY8_COMPLETE.md" ] && mv PHASE4_DAY8_COMPLETE.md archive/phase4-2025-09-to-10/01-daily-progress/day8-2025-10-07/

[ -f "PHASE4_DAYS9-10_COMPLETE.md" ] && mv PHASE4_DAYS9-10_COMPLETE.md archive/phase4-2025-09-to-10/01-daily-progress/days9-10-2025-10-08/

# Planning
[ -f "PHASE4_KICKOFF_PLAN.md" ] && mv PHASE4_KICKOFF_PLAN.md archive/phase4-2025-09-to-10/02-planning/
[ -f "PHASE4_CONTINUATION_PLAN.md" ] && mv PHASE4_CONTINUATION_PLAN.md archive/phase4-2025-09-to-10/02-planning/
[ -f "PHASE4_REMAINING_TASKS_DETAILED.md" ] && mv PHASE4_REMAINING_TASKS_DETAILED.md archive/phase4-2025-09-to-10/02-planning/

# Decisions
[ -f "PHASE4_DECISION_MADE.md" ] && mv PHASE4_DECISION_MADE.md archive/phase4-2025-09-to-10/03-decisions/
[ -f "PHASE4_ARCHITECTURE_INTEGRATION.md" ] && mv PHASE4_ARCHITECTURE_INTEGRATION.md archive/phase4-2025-09-to-10/03-decisions/

# Completion
[ -f "PHASE4_WEEK1_COMPLETE.md" ] && mv PHASE4_WEEK1_COMPLETE.md archive/phase4-2025-09-to-10/04-completion/

echo "✅ Phase 4 documents archived"
echo ""

# Step 3: Move session summaries
echo "📦 Archiving session summaries..."
[ -f "SESSION_SUMMARY_OCT8.md" ] && mv SESSION_SUMMARY_OCT8.md archive/sessions-2025-08-to-10/
[ -f "SESSION_ARCHITECTURE_CLEANUP.md" ] && mv SESSION_ARCHITECTURE_CLEANUP.md archive/sessions-2025-08-to-10/
[ -f "week3_day14_summary.md" ] && mv week3_day14_summary.md archive/sessions-2025-08-to-10/
echo "✅ Sessions archived"
echo ""

# Step 4: Move completed tasks
echo "📦 Archiving completed tasks..."
[ -f "TASK1_SEARCH_INTERFACE_COMPLETE.md" ] && mv TASK1_SEARCH_INTERFACE_COMPLETE.md archive/tasks-2025-09-to-10/
[ -f "TASK2_RESULT_VISUALIZATION_COMPLETE.md" ] && mv TASK2_RESULT_VISUALIZATION_COMPLETE.md archive/tasks-2025-09-to-10/
[ -f "TASK2_SEARCHAGENT_SEMANTIC_INTEGRATION.md" ] && mv TASK2_SEARCHAGENT_SEMANTIC_INTEGRATION.md archive/tasks-2025-09-to-10/
[ -f "TASK3_QUERY_ENHANCEMENT_COMPLETE.md" ] && mv TASK3_QUERY_ENHANCEMENT_COMPLETE.md archive/tasks-2025-09-to-10/
[ -f "TASK4_TESTING_PLAN.md" ] && mv TASK4_TESTING_PLAN.md archive/tasks-2025-09-to-10/
[ -f "ZERO_RESULTS_BUG_FIX.md" ] && mv ZERO_RESULTS_BUG_FIX.md archive/tasks-2025-09-to-10/
[ -f "ERROR_ANALYSIS_AND_RESOLUTION.md" ] && mv ERROR_ANALYSIS_AND_RESOLUTION.md archive/tasks-2025-09-to-10/
echo "✅ Tasks archived"
echo ""

# Step 5: Move current architecture docs
echo "📁 Moving current architecture docs..."
[ -f "SYSTEM_ARCHITECTURE.md" ] && mv SYSTEM_ARCHITECTURE.md current-2025-10/architecture/
[ -f "COMPLETE_ARCHITECTURE_OVERVIEW.md" ] && mv COMPLETE_ARCHITECTURE_OVERVIEW.md current-2025-10/architecture/
[ -f "DATA_FLOW_INTEGRATION_MAP.md" ] && mv DATA_FLOW_INTEGRATION_MAP.md current-2025-10/architecture/
[ -f "BACKEND_FRONTEND_CONTRACT.md" ] && mv BACKEND_FRONTEND_CONTRACT.md current-2025-10/architecture/
[ -f "COMPREHENSIVE_ARCHITECTURE_AUDIT.md" ] && mv COMPREHENSIVE_ARCHITECTURE_AUDIT.md current-2025-10/architecture/
echo "✅ Architecture docs moved"
echo ""

# Step 6: Move API docs
echo "📁 Moving API documentation..."
[ -f "API_REFERENCE.md" ] && mv API_REFERENCE.md current-2025-10/api/
[ -f "API_V2_REFERENCE.md" ] && mv API_V2_REFERENCE.md current-2025-10/api/
[ -f "API_ENDPOINT_MAPPING.md" ] && mv API_ENDPOINT_MAPPING.md current-2025-10/api/
[ -f "API_VERSIONING_ANALYSIS.md" ] && mv API_VERSIONING_ANALYSIS.md current-2025-10/api/
echo "✅ API docs moved"
echo ""

# Step 7: Move feature docs
echo "📁 Moving feature documentation..."
[ -f "AUTH_SYSTEM.md" ] && mv AUTH_SYSTEM.md current-2025-10/features/
[ -f "AGENT_FRAMEWORK_GUIDE.md" ] && mv AGENT_FRAMEWORK_GUIDE.md current-2025-10/features/
[ -f "AI_ANALYSIS_EXPLAINED.md" ] && mv AI_ANALYSIS_EXPLAINED.md current-2025-10/features/
[ -f "AI_ANALYSIS_FLOW_DIAGRAM.md" ] && mv AI_ANALYSIS_FLOW_DIAGRAM.md current-2025-10/features/
[ -f "AI_ANALYSIS_QUICK_REF.md" ] && mv AI_ANALYSIS_QUICK_REF.md current-2025-10/features/
[ -f "ADVANCED_SEARCH_FEATURES.md" ] && mv ADVANCED_SEARCH_FEATURES.md current-2025-10/features/
echo "✅ Feature docs moved"
echo ""

# Step 8: Move integration docs
echo "📁 Moving integration documentation..."
[ -f "INTEGRATION_LAYER_GUIDE.md" ] && mv INTEGRATION_LAYER_GUIDE.md current-2025-10/integration/
echo "✅ Integration docs moved"
echo ""

# Step 9: Rename old archive folders
echo "📁 Renaming old archive folders..."
if [ -d "archive/old_phases" ]; then
    mv archive/old_phases archive/phase0-2025-08-cleanup
fi
echo "✅ Archive folders renamed"
echo ""

# Step 10: Summary
echo "✨ Reorganization Complete!"
echo ""
echo "📊 New Structure:"
echo "  - current-2025-10/           Current docs (Oct 2025)"
echo "  - phase5-2025-10-to-2025-12/ Phase 5 work (Oct-Dec 2025)"
echo "  - archive/phase4-2025-09-to-10/ Phase 4 complete"
echo "  - archive/sessions-2025-08-to-10/ Session summaries"
echo "  - archive/tasks-2025-09-to-10/ Completed tasks"
echo ""
echo "📦 Backup location: $BACKUP_DIR"
echo ""
echo "✅ Ready for Phase 5!"
