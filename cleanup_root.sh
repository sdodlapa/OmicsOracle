#!/bin/bash
# Root folder cleanup script - Week 2 Day 4
# Organizes documentation, test files, and logs into appropriate folders
# Keeps only: README.md and CURRENT_STATUS.md in root

set -e

echo "🧹 Starting root folder cleanup..."

# Create necessary directories
mkdir -p docs/session_progress
mkdir -p docs/technical_analysis
mkdir -p docs/architecture
mkdir -p tests/week2
mkdir -p logs/archived

# Rename current status file to keep in root
echo "📌 Keeping WEEK2_DAY4_FINAL_STATUS.md as CURRENT_STATUS.md..."
cp WEEK2_DAY4_FINAL_STATUS.md CURRENT_STATUS.md 2>/dev/null || true

# Move Session Progress/Status Files (including the original)
echo "📋 Moving session progress files..."
mv WEEK2_DAY1_COMPLETE.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_DAY2_PROGRESS.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_DAY3_PARALLEL_OPTIMIZATION_SUMMARY.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_DAY3_PROGRESS.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_DAY4_COMPLETE_SUMMARY.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_DAY4_FINAL_STATUS.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_DAY4_IMPROVEMENTS_COMPLETE.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_DAY4_MIGRATION_PROGRESS.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_DAY4_SEARCHAGENT_MIGRATION_PLAN.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_DAY4_SESSION_PROGRESS.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_DAY4_SESSION_SUMMARY.md docs/session_progress/ 2>/dev/null || true
mv WEEK2_STATUS_AND_REMAINING_TASKS.md docs/session_progress/ 2>/dev/null || true
mv WEEK_2_INTEGRATION_PLAN.md docs/session_progress/ 2>/dev/null || true
mv SESSION_COMPLETE_WEEK2_DAY3.md docs/session_progress/ 2>/dev/null || true
mv GIT_STATUS_CLEAN.md docs/session_progress/ 2>/dev/null || true

# Move Technical Analysis Documents
echo "📊 Moving technical analysis files..."
mv ACTUAL_BOTTLENECK_ANALYSIS.md docs/technical_analysis/ 2>/dev/null || true
mv CACHE_TEST_BOTTLENECK_ANALYSIS.md docs/technical_analysis/ 2>/dev/null || true
mv CITATION_FILTERING_STRATEGY.md docs/technical_analysis/ 2>/dev/null || true
mv CORRECTED_BOTTLENECK_ANALYSIS.md docs/technical_analysis/ 2>/dev/null || true
mv DEDUPLICATION_ANALYSIS.md docs/technical_analysis/ 2>/dev/null || true
mv FILE_LOGGING_GUIDE.md docs/technical_analysis/ 2>/dev/null || true
mv LOGGING_IMPLEMENTATION_SUMMARY.md docs/technical_analysis/ 2>/dev/null || true
mv LOG_ANALYSIS_AND_IMPROVEMENTS.md docs/technical_analysis/ 2>/dev/null || true
mv PARALLEL_DOWNLOAD_OPTIMIZATION_COMPLETE.md docs/technical_analysis/ 2>/dev/null || true

# Move Architecture/Design Documents
echo "🏗️  Moving architecture documents..."
mv CRITICAL_CLARIFICATION_GEO_DATA.md docs/architecture/ 2>/dev/null || true
mv DATA_COLLECTION_VS_DOWNLOAD_ARCHITECTURE.md docs/architecture/ 2>/dev/null || true
mv ENHANCEMENT_FTP_LINK_COLLECTION.md docs/architecture/ 2>/dev/null || true
mv LLM_CITATION_ANALYSIS_CONTROL.md docs/architecture/ 2>/dev/null || true
mv VALUE_OF_SOFT_METADATA_FILES.md docs/architecture/ 2>/dev/null || true

# Move Test Files
echo "🧪 Moving test files..."
mv test_parallel_download.py tests/week2/ 2>/dev/null || true
mv test_query_optimizer_integration.py tests/week2/ 2>/dev/null || true
mv test_quick_migration.py tests/week2/ 2>/dev/null || true
mv test_searchagent_migration.py tests/week2/ 2>/dev/null || true
mv test_searchagent_migration_with_logging.py tests/week2/ 2>/dev/null || true
mv test_unified_pipeline.py tests/week2/ 2>/dev/null || true
mv test_week2_cache_integration.py tests/week2/ 2>/dev/null || true
mv test_week2_day4_improvements.py tests/week2/ 2>/dev/null || true
mv test_week2_geo_integration.py tests/week2/ 2>/dev/null || true
mv test_week2_publication_integration.py tests/week2/ 2>/dev/null || true
mv quick_test.py tests/week2/ 2>/dev/null || true

# Move Log Files
echo "📝 Moving log files..."
mv week2_day1_geo_test.log logs/archived/ 2>/dev/null || true
mv week2_day1_geo_test_fixed.log logs/archived/ 2>/dev/null || true
mv week2_day2_publication_test.log logs/archived/ 2>/dev/null || true
mv week2_day3_cache_test.log logs/archived/ 2>/dev/null || true
mv parallel_test_output.log logs/archived/ 2>/dev/null || true
mv fulltext_validation_log.txt logs/archived/ 2>/dev/null || true
mv robust_search_log.txt logs/archived/ 2>/dev/null || true

# Move JSON result files
echo "📦 Moving result files..."
mv fulltext_validation_results.json logs/archived/ 2>/dev/null || true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📁 Files organized into:"
echo "  - docs/session_progress/     (15 files)"
echo "  - docs/technical_analysis/   (9 files)"
echo "  - docs/architecture/         (5 files)"
echo "  - tests/week2/              (11 files)"
echo "  - logs/archived/            (8 files)"
echo ""
echo "🎯 Root folder is now clean and organized!"
