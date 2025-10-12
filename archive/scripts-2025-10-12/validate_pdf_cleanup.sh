#!/bin/bash
# Quick validation script to ensure no broken code remains

echo "=============================================="
echo "  PDF Download Cleanup Validation"
echo "=============================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Test 1: Check for download_utils imports (excluding archive)
echo "Test 1: Checking for deprecated download_utils imports..."
MATCHES=$(grep -r "from omics_oracle_v2.lib.fulltext.download_utils import" omics_oracle_v2/ --include=*.py 2>/dev/null | grep -v "archive" || true)
if [ -z "$MATCHES" ]; then
    echo -e "${GREEN}✓ PASS${NC}: No deprecated imports found"
else
    echo -e "${RED}✗ FAIL${NC}: Found deprecated imports:"
    echo "$MATCHES"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 2: Verify PDFDownloadManager is used
echo "Test 2: Verifying PDFDownloadManager usage..."
if grep -q "from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager" omics_oracle_v2/api/routes/agents.py; then
    echo -e "${GREEN}✓ PASS${NC}: API endpoint imports PDFDownloadManager"
else
    echo -e "${RED}✗ FAIL${NC}: API endpoint missing PDFDownloadManager import"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 3: Check syntax of modified files
echo "Test 3: Checking Python syntax..."
FILES_TO_CHECK=(
    "omics_oracle_v2/lib/fulltext/manager.py"
    "omics_oracle_v2/api/routes/agents.py"
    "omics_oracle_v2/lib/publications/models.py"
)

for FILE in "${FILES_TO_CHECK[@]}"; do
    if python -m py_compile "$FILE" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $FILE"
    else
        echo -e "${RED}✗${NC} $FILE (syntax error)"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Test 4: Verify download_utils is archived
echo "Test 4: Verifying download_utils.py is archived..."
if [ -f "omics_oracle_v2/lib/archive/deprecated_20251012/download_utils.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}: download_utils.py archived"
else
    echo -e "${RED}✗ FAIL${NC}: download_utils.py not found in archive"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "omics_oracle_v2/lib/fulltext/download_utils.py" ]; then
    echo -e "${RED}✗ FAIL${NC}: download_utils.py still exists in fulltext/"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ PASS${NC}: download_utils.py removed from fulltext/"
fi
echo ""

# Test 5: Verify Publication model has fulltext_url
echo "Test 5: Checking Publication model fields..."
if grep -q "fulltext_url: Optional\[str\]" omics_oracle_v2/lib/publications/models.py; then
    echo -e "${GREEN}✓ PASS${NC}: Publication model has fulltext_url field"
else
    echo -e "${RED}✗ FAIL${NC}: Publication model missing fulltext_url field"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Summary
echo "=============================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Restart server: ./start_omics_oracle.sh"
    echo "  2. Test download via dashboard"
    echo "  3. Run: python test_pdf_download_integration.py"
    exit 0
else
    echo -e "${RED}✗ $ERRORS TEST(S) FAILED${NC}"
    echo ""
    echo "Please fix the errors before proceeding."
    exit 1
fi
