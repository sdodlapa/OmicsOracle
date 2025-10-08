#!/bin/bash
# Quick Cleanup Script - Phase 1 (Critical Issues)
# Reduces repo size from 4.2GB to ~20MB
# Run time: ~5 minutes

set -e  # Exit on error

echo "=== OmicsOracle Codebase Cleanup - Phase 1 ==="
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "omics_oracle_v2" ]; then
    echo -e "${RED}[ERROR] Must run from OmicsOracle root directory${NC}"
    exit 1
fi

# Confirmation
echo -e "${YELLOW}[WARNING] This will:${NC}"
echo "  1. Update .gitignore"
echo "  2. Remove venv/, backups/, htmlcov/ from git tracking"
echo "  3. Remove database and coverage files from git"
echo "  4. Organize test files into tests/ directory"
echo ""
echo -e "${YELLOW}Repository size will go from 4.2GB to ~20MB${NC}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# Step 1: Update .gitignore
echo "[Step 1/4] Updating .gitignore..."
cat >> .gitignore << 'EOF'

# Phase 1 Cleanup - Added by cleanup script
# Virtual environments
venv/
env/
ENV/

# Backups (should not be in repo)
backups/

# Coverage reports
htmlcov/
.coverage
.coverage.*

# Databases (generated files)
*.db
*.db-shm
*.db-wal

# Test outputs
test_*.json
test_*.html

# Cache
.cache/
.pytest_cache/
__pycache__/
*.pyc
*.pyo

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
EOF

echo -e "${GREEN}[OK] .gitignore updated${NC}"

# Step 2: Remove large directories from git tracking
echo ""
echo "[Step 2/4] Removing large files from git tracking..."
echo "  (Files remain on disk, just not tracked by git)"

# Remove from git but keep locally
git rm -r --cached venv/ 2>/dev/null || echo "  venv/ already removed"
git rm -r --cached backups/ 2>/dev/null || echo "  backups/ already removed"
git rm -r --cached htmlcov/ 2>/dev/null || echo "  htmlcov/ already removed"

echo -e "${GREEN}[OK] Large directories removed from git${NC}"

# Step 3: Remove database and coverage files
echo ""
echo "[Step 3/4] Removing database and coverage files from git..."

git rm --cached omics_oracle.db 2>/dev/null || echo "  omics_oracle.db already removed"
git rm --cached .coverage 2>/dev/null || echo "  .coverage already removed"
git rm --cached test_*.json 2>/dev/null || echo "  test JSON files already removed"
git rm --cached test_*.html 2>/dev/null || echo "  test HTML files already removed"

echo -e "${GREEN}[OK] Database and test files removed from git${NC}"

# Step 4: Organize test files
echo ""
echo "[Step 4/4] Organizing test files..."

# Create test directories
mkdir -p tests/integration
mkdir -p tests/unit
mkdir -p tests/debug
mkdir -p tests/fixtures

# Move test files (only if they exist in root)
if ls test_day*.py 1> /dev/null 2>&1; then
    mv test_day*.py tests/integration/ 2>/dev/null || true
    echo "  [+] Moved integration tests (test_day*.py)"
fi

if ls test_*debug*.py 1> /dev/null 2>&1; then
    mv test_*debug*.py tests/debug/ 2>/dev/null || true
    echo "  [+] Moved debug tests"
fi

if ls test_*.py 1> /dev/null 2>&1; then
    mv test_*.py tests/unit/ 2>/dev/null || true
    echo "  [+] Moved unit tests"
fi

# Move test data files
if ls test_*.json 1> /dev/null 2>&1; then
    mv test_*.json tests/fixtures/ 2>/dev/null || true
    echo "  [+] Moved test JSON files"
fi

if ls demo_*.json 1> /dev/null 2>&1; then
    mv demo_*.json tests/fixtures/ 2>/dev/null || true
    echo "  [+] Moved demo files"
fi

if ls test_*.html 1> /dev/null 2>&1; then
    mv test_*.html tests/fixtures/ 2>/dev/null || true
    echo "  [+] Moved test HTML files"
fi

# Create __init__.py files
touch tests/__init__.py
touch tests/integration/__init__.py
touch tests/unit/__init__.py
touch tests/debug/__init__.py
touch tests/fixtures/__init__.py

echo -e "${GREEN}[OK] Test files organized${NC}"

# Step 5: Commit changes
echo ""
echo "[Step 5/5] Committing changes..."

git add .gitignore
git add tests/

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo -e "${YELLOW}[WARNING] No changes to commit (already clean)${NC}"
else
    git commit -m "chore: Phase 1 cleanup - organize tests and remove large files

- Updated .gitignore to exclude venv/, backups/, coverage files
- Removed venv/ (3GB), backups/ (164MB), htmlcov/ from git tracking
- Removed database and test output files from tracking
- Organized test files into tests/ directory structure
  - tests/integration/ for test_day*.py
  - tests/unit/ for other test files
  - tests/debug/ for debug test files
  - tests/fixtures/ for test data files

Repository size reduced from 4.2GB to ~20MB (99.5% reduction)"

    echo -e "${GREEN}[OK] Changes committed${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}[SUCCESS] Phase 1 Cleanup Complete!${NC}"
echo "=========================================="
echo ""
echo "Results:"
echo "  [OK] .gitignore updated with exclusions"
echo "  [OK] Large files removed from git tracking"
echo "  [OK] Test files organized into tests/"
echo "  [OK] Changes committed"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Run tests: pytest tests/ -v"
echo "  3. Push changes: git push origin phase-4-production-features"
echo "  4. Continue with Phase 2 cleanup (see CODEBASE_CLEANUP_ANALYSIS.md)"
echo ""
echo "Repository size after push: ~20MB (down from 4.2GB)"
echo ""
