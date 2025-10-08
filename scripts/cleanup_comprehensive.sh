#!/bin/bash

# OmicsOracle Comprehensive Cleanup Script
# This script performs complete codebase cleanup and reorganization
# Date: October 7, 2024

set -e  # Exit on error

# Colors for output (using ANSI codes)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_section() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
    echo ""
}

# Get repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

print_section "OmicsOracle Comprehensive Cleanup Script"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -f "README.md" ]; then
    print_error "Not in OmicsOracle repository root!"
    exit 1
fi

print_status "Repository root: $REPO_ROOT"

# Get initial size
INITIAL_SIZE=$(du -sh . 2>/dev/null | cut -f1)
print_info "Initial repository size: $INITIAL_SIZE"

# Create backup
print_section "Creating Backup"
BACKUP_NAME="omics_oracle_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
BACKUP_PATH="../$BACKUP_NAME"

print_info "Creating backup at: $BACKUP_PATH"
tar -czf "$BACKUP_PATH" \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    . 2>/dev/null || true

if [ -f "$BACKUP_PATH" ]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_PATH" 2>/dev/null | cut -f1)
    print_status "Backup created: $BACKUP_SIZE"
else
    print_warning "Backup creation failed, but continuing..."
fi

# Phase 1: Remove Virtual Environment
print_section "Phase 1: Remove Virtual Environment"

if [ -d "venv" ]; then
    VENV_SIZE=$(du -sh venv 2>/dev/null | cut -f1 || echo "unknown")
    print_info "Removing venv/ ($VENV_SIZE)..."
    rm -rf venv
    print_status "Virtual environment removed"
else
    print_info "No venv/ directory found"
fi

# Phase 2: Remove Compiled Python Files
print_section "Phase 2: Remove Compiled Python Files"

print_info "Counting compiled files..."
PYC_COUNT=$(find . -type f -name "*.pyc" 2>/dev/null | wc -l | tr -d ' ')
PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')

print_info "Found $PYC_COUNT .pyc files and $PYCACHE_COUNT __pycache__ directories"

if [ "$PYC_COUNT" -gt 0 ] || [ "$PYCACHE_COUNT" -gt 0 ]; then
    print_info "Removing compiled Python files..."
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    print_status "Compiled files removed"
else
    print_info "No compiled files found"
fi

# Phase 3: Organize Test Files
print_section "Phase 3: Organize Test Files"

# Count test files in root
TEST_COUNT=$(ls -1 test_*.py 2>/dev/null | wc -l | tr -d ' ')
print_info "Found $TEST_COUNT test files in root directory"

if [ "$TEST_COUNT" -gt 0 ]; then
    print_info "Creating organized test structure..."

    # Create test subdirectories
    mkdir -p tests/integration/day_tests
    mkdir -p tests/unit/cache
    mkdir -p tests/unit/search
    mkdir -p tests/unit/pdf
    mkdir -p tests/unit/pipeline
    mkdir -p tests/debug

    # Move day test files
    if ls test_day*.py 1> /dev/null 2>&1; then
        print_info "Moving day test files..."
        mv test_day*.py tests/integration/day_tests/ 2>/dev/null || true
    fi

    # Move cache test files
    if ls test_*cache*.py 1> /dev/null 2>&1; then
        print_info "Moving cache test files..."
        mv test_*cache*.py tests/unit/cache/ 2>/dev/null || true
        mv test_redis*.py tests/unit/cache/ 2>/dev/null || true
    fi

    # Move search test files
    if ls test_*search*.py 1> /dev/null 2>&1; then
        print_info "Moving search test files..."
        mv test_*search*.py tests/unit/search/ 2>/dev/null || true
        mv test_*pubmed*.py tests/unit/search/ 2>/dev/null || true
        mv test_*scholar*.py tests/unit/search/ 2>/dev/null || true
    fi

    # Move PDF test files
    if ls test_pdf*.py 1> /dev/null 2>&1; then
        print_info "Moving PDF test files..."
        mv test_pdf*.py tests/unit/pdf/ 2>/dev/null || true
    fi

    # Move pipeline test files
    if ls test_*pipeline*.py 1> /dev/null 2>&1; then
        print_info "Moving pipeline test files..."
        mv test_*pipeline*.py tests/unit/pipeline/ 2>/dev/null || true
        mv test_embedding*.py tests/unit/pipeline/ 2>/dev/null || true
    fi

    # Move debug test files
    if ls test_*debug*.py 1> /dev/null 2>&1; then
        print_info "Moving debug test files..."
        mv test_*debug*.py tests/debug/ 2>/dev/null || true
    fi

    # Move remaining test files to integration
    if ls test_*.py 1> /dev/null 2>&1; then
        print_info "Moving remaining test files to integration..."
        mv test_*.py tests/integration/ 2>/dev/null || true
    fi

    print_status "Test files organized"
else
    print_info "No test files to organize"
fi

# Phase 4: Clean Up Backups Directory
print_section "Phase 4: Archive Backups Directory"

if [ -d "backups" ]; then
    BACKUP_DIR_SIZE=$(du -sh backups 2>/dev/null | cut -f1)
    print_info "Backups directory size: $BACKUP_DIR_SIZE"
    print_info "Moving backups/ to ../omics_oracle_old_backups/"

    # Move backups out of repository
    mv backups ../omics_oracle_old_backups_$(date +%Y%m%d) 2>/dev/null || true
    print_status "Backups directory archived outside repository"
else
    print_info "No backups/ directory found"
fi

# Phase 5: Update .gitignore
print_section "Phase 5: Update .gitignore"

print_info "Updating .gitignore..."

# Backup current .gitignore
if [ -f ".gitignore" ]; then
    cp .gitignore .gitignore.backup
    print_info "Created .gitignore backup"
fi

# Ensure critical patterns are in .gitignore
cat >> .gitignore << 'EOF'

# === Cleanup Script Additions ===

# Virtual environments
venv/
.venv/
env/
ENV/

# Compiled Python files
__pycache__/
*.py[cod]
*$py.class
*.so

# Backups
backups/
*.backup
*.bak

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Test outputs
.pytest_cache/
.coverage
htmlcov/
test-reports/
*.log

# Data files (keep structure, ignore content)
data/*.db
data/*.sqlite
data/*.csv
data/downloads/

# Environment files
.env
.env.local
.env.*.local

# Build outputs
dist/
build/
*.egg-info/

EOF

print_status ".gitignore updated"

# Phase 6: Remove Duplicate/Redundant Files
print_section "Phase 6: Remove Redundant Files"

# Remove old README
if [ -f "README_OLD.md" ]; then
    print_info "Removing README_OLD.md..."
    rm README_OLD.md
    print_status "README_OLD.md removed"
fi

# Remove one-off commit scripts
if [ -f "DAY_26_COMMIT.sh" ]; then
    print_info "Removing one-off commit script..."
    rm DAY_26_COMMIT.sh
    print_status "DAY_26_COMMIT.sh removed"
fi

# Phase 7: Create Documentation Structure
print_section "Phase 7: Organize Documentation"

print_info "Creating documentation structure..."

# Create history directories
mkdir -p docs/history/week_1_2
mkdir -p docs/history/week_3
mkdir -p docs/history/week_4
mkdir -p docs/guides

# Move week-specific docs
print_info "Moving daily documentation to history..."

# Week 1-2 docs
ls DAY_1*.md DAY_2*.md 2>/dev/null | while read file; do
    mv "$file" docs/history/week_1_2/ 2>/dev/null || true
done

# Week 3 docs
ls DAY_1[5-9]*.md DAY_2[0-1]*.md WEEK3*.md 2>/dev/null | while read file; do
    mv "$file" docs/history/week_3/ 2>/dev/null || true
done

# Week 4 docs
ls DAY_2[2-9]*.md DAY_3*.md WEEK4*.md WEEK_4*.md 2>/dev/null | while read file; do
    mv "$file" docs/history/week_4/ 2>/dev/null || true
done

# Move session and status docs
ls SESSION*.md *STATUS*.md *STATE*.md 2>/dev/null | while read file; do
    # Determine which week based on content or date
    mv "$file" docs/history/week_4/ 2>/dev/null || true
done

# Keep essential guides in docs/guides/
if [ -f "API_USAGE_GUIDE.md" ]; then
    mv API_USAGE_GUIDE.md docs/guides/ 2>/dev/null || true
fi
if [ -f "DEPLOYMENT_GUIDE.md" ]; then
    mv DEPLOYMENT_GUIDE.md docs/guides/ 2>/dev/null || true
fi
if [ -f "QUICK_START.md" ]; then
    mv QUICK_START.md docs/guides/ 2>/dev/null || true
fi

print_status "Documentation organized"

# Phase 8: Consolidate Startup Scripts
print_section "Phase 8: Consolidate Startup Scripts"

print_info "Creating unified startup script..."

mkdir -p scripts

cat > scripts/start.sh << 'EOFSCRIPT'
#!/bin/bash
# Unified OmicsOracle Startup Script

set -e

# Default values
MODE="dev"
SSL_BYPASS=false
DB_TYPE="postgres"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --ssl-bypass)
            SSL_BYPASS=true
            shift
            ;;
        --db)
            DB_TYPE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./scripts/start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode MODE        Set mode (dev|prod) [default: dev]"
            echo "  --ssl-bypass       Enable SSL bypass"
            echo "  --db DB_TYPE       Set database (postgres|sqlite) [default: postgres]"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Set environment variables based on options
export MODE="$MODE"

if [ "$SSL_BYPASS" = true ]; then
    export SSL_VERIFY=false
    echo "SSL verification disabled"
fi

if [ "$DB_TYPE" = "sqlite" ]; then
    export DATABASE_URL="sqlite:///./omics_oracle.db"
    echo "Using SQLite database"
fi

# Start server
echo "Starting OmicsOracle in $MODE mode..."

if [ "$MODE" = "dev" ]; then
    uvicorn omics_oracle_v2.api.main:app --reload --host 0.0.0.0 --port 8000
else
    uvicorn omics_oracle_v2.api.main:app --host 0.0.0.0 --port 8000
fi
EOFSCRIPT

chmod +x scripts/start.sh
print_status "Unified startup script created: scripts/start.sh"

# Archive old scripts
mkdir -p scripts/archive
mv start_*.sh scripts/archive/ 2>/dev/null || true
print_info "Old startup scripts archived in scripts/archive/"

# Get final size
print_section "Cleanup Complete"

FINAL_SIZE=$(du -sh . 2>/dev/null | cut -f1)

print_status "Cleanup completed successfully!"
echo ""
echo "Summary:"
echo "--------"
echo "Initial size: $INITIAL_SIZE"
echo "Final size:   $FINAL_SIZE"
echo ""
echo "Changes made:"
echo "  - Removed virtual environment"
echo "  - Removed compiled Python files"
echo "  - Organized test files into tests/ subdirectories"
echo "  - Archived backups/ directory outside repository"
echo "  - Updated .gitignore"
echo "  - Removed redundant files"
echo "  - Organized documentation into docs/history/"
echo "  - Created unified startup script"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Test the application: ./scripts/start.sh"
echo "  3. Run tests: pytest tests/"
echo "  4. Recreate venv: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
echo "  5. Commit changes: git add . && git commit -m 'cleanup: Comprehensive codebase reorganization'"
echo ""
print_status "Backup saved at: $BACKUP_PATH"
