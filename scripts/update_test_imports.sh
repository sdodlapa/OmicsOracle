#!/bin/bash
# Script to update test file imports for pipeline reorganization
# Author: OmicsOracle Team
# Date: October 14, 2025

echo "======================================================================"
echo "Updating Test File Imports"
echo "======================================================================"
echo ""

# Define the files to update
test_files=(
    "tests/test_scihub.py"
    "tests/test_fulltext_manager.py"
    "tests/test_detailed_breakdown.py"
    "tests/test_scihub_response_debug.py"
    "tests/test_single_doi_debug.py"
    "tests/test_scihub_fills_gaps.py"
    "tests/test_identify_failures.py"
    "tests/test_comprehensive_fulltext_validation.py"
    "tests/fulltext/test_integration.py"
    "tests/test_geo_citation_pipeline_integration.py"
    "tests/test_scihub_full_html.py"
    "tests/test_scihub_strategies.py"
    "tests/week3/test_session_cleanup.py"
    "tests/lib/fulltext/test_normalizer.py"
    "tests/lib/fulltext/test_smart_cache.py"
    "tests/lib/fulltext/test_parsed_cache.py"
    "tests/lib/fulltext/test_cache_db.py"
    "tests/test_phase1_phase2.py"
    "tests/test_pipeline_1_2_integration.py"
    "tests/test_scihub_debug.py"
)

echo "Will update ${#test_files[@]} test files..."
echo ""

# Backup first
echo "Creating backup..."
tar -czf tests_backup_$(date +%Y%m%d_%H%M%S).tar.gz tests/
echo "✓ Backup created"
echo ""

# Update imports using sed
for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "Updating: $file"
        
        # Pipeline 2: URL Collection (manager, sources)
        sed -i.bak 's|from omics_oracle_v2\.lib\.enrichment\.fulltext\.manager|from omics_oracle_v2.lib.pipelines.url_collection.manager|g' "$file"
        sed -i.bak 's|from omics_oracle_v2\.lib\.enrichment\.fulltext\.sources|from omics_oracle_v2.lib.pipelines.url_collection.sources|g' "$file"
        
        # Pipeline 3: PDF Download (download_manager, smart_cache, utils)
        sed -i.bak 's|from omics_oracle_v2\.lib\.enrichment\.fulltext\.download_manager|from omics_oracle_v2.lib.pipelines.pdf_download.download_manager|g' "$file"
        sed -i.bak 's|from omics_oracle_v2\.lib\.enrichment\.fulltext\.smart_cache|from omics_oracle_v2.lib.pipelines.pdf_download.smart_cache|g' "$file"
        sed -i.bak 's|from omics_oracle_v2\.lib\.enrichment\.fulltext\.utils|from omics_oracle_v2.lib.pipelines.pdf_download.utils|g' "$file"
        
        # Pipeline 4: Text Enrichment (pdf_parser, parsed_cache, cache_db, normalizer)
        sed -i.bak 's|from omics_oracle_v2\.lib\.enrichment\.fulltext\.pdf_parser|from omics_oracle_v2.lib.pipelines.text_enrichment.pdf_parser|g' "$file"
        sed -i.bak 's|from omics_oracle_v2\.lib\.enrichment\.fulltext\.parsed_cache|from omics_oracle_v2.lib.pipelines.text_enrichment.parsed_cache|g' "$file"
        sed -i.bak 's|from omics_oracle_v2\.lib\.enrichment\.fulltext\.cache_db|from omics_oracle_v2.lib.pipelines.text_enrichment.cache_db|g' "$file"
        sed -i.bak 's|from omics_oracle_v2\.lib\.enrichment\.fulltext\.normalizer|from omics_oracle_v2.lib.pipelines.text_enrichment.normalizer|g' "$file"
        
        # Clean up backup files
        rm -f "${file}.bak"
        
        echo "  ✓ Updated"
    else
        echo "  ⚠ File not found: $file"
    fi
done

echo ""
echo "======================================================================"
echo "✓ All test imports updated!"
echo "======================================================================"
echo ""
echo "Next: Run 'pytest tests/' to verify tests still pass"
