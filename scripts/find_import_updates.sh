#!/bin/bash
# Script to find all imports that need updating for pipeline reorganization
# Author: OmicsOracle Team
# Date: October 14, 2025

echo "======================================================================"
echo "PIPELINE REORGANIZATION - IMPORT FINDER"
echo "======================================================================"
echo ""

echo "----------------------------------------------------------------------"
echo "PIPELINE 1: URL COLLECTION"
echo "----------------------------------------------------------------------"
echo ""
echo "Files to update in url_collection pipeline:"
find omics_oracle_v2/lib/pipelines/url_collection -name "*.py" -type f | sort
echo ""

echo "Old imports to replace (from enrichment.fulltext):"
grep -n "from omics_oracle_v2.lib.enrichment.fulltext" omics_oracle_v2/lib/pipelines/url_collection/**/*.py 2>/dev/null | head -30
echo ""

echo "----------------------------------------------------------------------"
echo "PIPELINE 2: PDF DOWNLOAD"
echo "----------------------------------------------------------------------"
echo ""
echo "Files to update in pdf_download pipeline:"
find omics_oracle_v2/lib/pipelines/pdf_download -name "*.py" -type f | sort
echo ""

echo "Old imports to replace:"
grep -n "from omics_oracle_v2.lib.enrichment.fulltext" omics_oracle_v2/lib/pipelines/pdf_download/**/*.py 2>/dev/null
echo ""

echo "----------------------------------------------------------------------"
echo "PIPELINE 3: TEXT ENRICHMENT"
echo "----------------------------------------------------------------------"
echo ""
echo "Files to update in text_enrichment pipeline:"
find omics_oracle_v2/lib/pipelines/text_enrichment -name "*.py" -type f | sort
echo ""

echo "Old imports to replace:"
grep -n "from omics_oracle_v2.lib.enrichment.fulltext" omics_oracle_v2/lib/pipelines/text_enrichment/**/*.py 2>/dev/null
echo ""

echo "----------------------------------------------------------------------"
echo "API INTEGRATION POINTS"
echo "----------------------------------------------------------------------"
echo ""
echo "API routes using fulltext imports:"
grep -n "from omics_oracle_v2.lib.enrichment.fulltext" omics_oracle_v2/api/routes/*.py 2>/dev/null
echo ""

echo "----------------------------------------------------------------------"
echo "TEST FILES"
echo "----------------------------------------------------------------------"
echo ""
echo "Test files using fulltext imports:"
grep -rn "from omics_oracle_v2.lib.enrichment.fulltext" tests/ 2>/dev/null | head -20
echo ""

echo "----------------------------------------------------------------------"
echo "SUMMARY OF IMPORT REPLACEMENTS NEEDED"
echo "----------------------------------------------------------------------"
echo ""
echo "Replace patterns:"
echo "  OLD: from omics_oracle_v2.lib.enrichment.fulltext.manager"
echo "  NEW: from omics_oracle_v2.lib.pipelines.url_collection.manager"
echo ""
echo "  OLD: from omics_oracle_v2.lib.enrichment.fulltext.download_manager"
echo "  NEW: from omics_oracle_v2.lib.pipelines.pdf_download.download_manager"
echo ""
echo "  OLD: from omics_oracle_v2.lib.enrichment.fulltext.pdf_parser"
echo "  NEW: from omics_oracle_v2.lib.pipelines.text_enrichment.pdf_parser"
echo ""
echo "  OLD: from omics_oracle_v2.lib.enrichment.fulltext.sources"
echo "  NEW: from omics_oracle_v2.lib.pipelines.url_collection.sources"
echo ""
echo "  OLD: from omics_oracle_v2.lib.enrichment.fulltext.utils"
echo "  NEW: from omics_oracle_v2.lib.pipelines.pdf_download.utils"
echo ""
echo "======================================================================"
echo "END OF REPORT"
echo "======================================================================"
