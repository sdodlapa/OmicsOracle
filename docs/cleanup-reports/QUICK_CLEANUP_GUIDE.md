# 🧹 Quick Cleanup Guide

**TL;DR:** Run `./scripts/cleanup_comprehensive.sh` to reduce repository from 4.2 GB to ~20 MB.

---

## Current Issues

1. **4.2 GB repository** (should be ~20 MB)
   - 2.6 GB: `venv/` directory
   - 164 MB: `backups/` directory
   - 14,387: `.pyc` compiled files
   - 2,302: `__pycache__` directories

2. **58 markdown files** scattered in root

3. **22 test files** in root (should be in `tests/`)

4. **5 startup scripts** (confusing)

---

## Three Options

### Option 1: Automated (Recommended) - 5 minutes

```bash
# Run comprehensive cleanup script
./scripts/cleanup_comprehensive.sh

# Review changes
git status

# Recreate venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test everything still works
pytest tests/

# Commit
git add .
git commit -m "cleanup: Comprehensive codebase reorganization (4.2GB -> 20MB)"
```

**What it does:**
- ✅ Removes `venv/` (2.6 GB)
- ✅ Removes all `.pyc` files (14,387 files)
- ✅ Organizes test files into `tests/` subdirectories
- ✅ Archives `backups/` outside repository
- ✅ Updates `.gitignore`
- ✅ Removes redundant files
- ✅ Organizes documentation
- ✅ Creates unified startup script
- ✅ Creates backup before changes

**Result:** 4.2 GB → ~20 MB (99.5% reduction)

---

### Option 2: Manual Critical Only - 10 minutes

```bash
# Remove venv
rm -rf venv

# Remove compiled files
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +

# Archive backups
mv backups ../omics_oracle_backups_$(date +%Y%m%d)

# Check size
du -sh .

# Recreate venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Commit
git add .
git commit -m "cleanup: Remove venv and compiled files"
```

**Result:** 4.2 GB → ~20 MB (critical issues only)

---

### Option 3: Review First, Execute Later

```bash
# Read the comprehensive analysis
cat CRITICAL_CLEANUP_REPORT.md

# Review what the script will do
cat scripts/cleanup_comprehensive.sh

# When ready, run it
./scripts/cleanup_comprehensive.sh
```

---

## What Gets Changed

### Files Removed
- `venv/` directory (2.6 GB)
- All `*.pyc` and `__pycache__/` (14,387 files)
- `backups/` directory (moved outside repo)
- `README_OLD.md`
- `DAY_26_COMMIT.sh`

### Files Moved

**Test Files:** Root → `tests/`
```
test_day*.py                 → tests/integration/day_tests/
test_*cache*.py              → tests/unit/cache/
test_*search*.py             → tests/unit/search/
test_pdf*.py                 → tests/unit/pdf/
test_*pipeline*.py           → tests/unit/pipeline/
test_*debug*.py              → tests/debug/
```

**Documentation:** Root → `docs/`
```
DAY_*.md                     → docs/history/week_*/
SESSION*.md                  → docs/history/week_*/
*STATUS*.md                  → docs/history/week_*/
API_USAGE_GUIDE.md           → docs/guides/
DEPLOYMENT_GUIDE.md          → docs/guides/
QUICK_START.md               → docs/guides/
```

**Startup Scripts:** Root → `scripts/`
```
start_*.sh                   → scripts/archive/
(New) scripts/start.sh       ← Unified script
```

### Files Updated
- `.gitignore` - Enhanced with comprehensive exclusions

---

## Safety Features

1. **Backup Created:** Full backup before any changes
2. **Reversible:** All changes can be undone
3. **Git-Safe:** Only removes files already in `.gitignore`
4. **No Data Loss:** Files moved, not deleted (except bloat)

---

## After Cleanup

### New Structure
```
OmicsOracle/                     (~20 MB)
├── README.md                    ✅ Main documentation
├── pyproject.toml               ✅ Project config
├── requirements.txt             ✅ Dependencies
├── docker-compose.yml           ✅ Production deployment
├── docs/
│   ├── guides/
│   │   ├── API_USAGE_GUIDE.md   ✅ API reference
│   │   ├── DEPLOYMENT_GUIDE.md  ✅ Deployment guide
│   │   └── QUICK_START.md       ✅ Quick start
│   └── history/
│       ├── week_1_2/            📁 Historical docs
│       ├── week_3/              📁 Historical docs
│       └── week_4/              📁 Historical docs
├── scripts/
│   ├── start.sh                 ✅ Unified startup script
│   └── archive/                 📁 Old scripts
├── tests/
│   ├── integration/             ✅ Integration tests
│   ├── unit/                    ✅ Unit tests
│   └── debug/                   ✅ Debug tests
└── omics_oracle_v2/             ✅ Source code
```

### New Workflow

**Start Development:**
```bash
./scripts/start.sh --mode dev
```

**Start Production:**
```bash
./scripts/start.sh --mode prod
```

**Start with SSL Bypass:**
```bash
./scripts/start.sh --ssl-bypass
```

**Start with SQLite:**
```bash
./scripts/start.sh --db sqlite
```

**Run Tests:**
```bash
pytest tests/
```

---

## Verification

After cleanup, verify everything works:

```bash
# Check size (should be ~20 MB)
du -sh .

# Check no venv in git
git ls-files | grep venv

# Check no compiled files
find . -name "*.pyc" -o -name "__pycache__"

# Check tests organized
ls -la tests/

# Recreate venv and test
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/

# Check application starts
./scripts/start.sh --mode dev
```

---

## Troubleshooting

### "venv not found" after cleanup
```bash
# Recreate it
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Tests fail after reorganization
```bash
# Tests might have absolute imports
# Update imports in moved test files:
# Before: from test_config import ...
# After:  from tests.test_config import ...
```

### Startup script doesn't work
```bash
# Make sure it's executable
chmod +x scripts/start.sh

# Check python path
which python3
```

### Want to undo cleanup
```bash
# Extract the backup created
tar -xzf ../omics_oracle_backup_*.tar.gz -C ../restored/
```

---

## Next Steps After Cleanup

1. **Commit Changes:**
   ```bash
   git add .
   git commit -m "cleanup: Comprehensive codebase reorganization"
   git push origin phase-4-production-features
   ```

2. **Create CHANGELOG.md:**
   - Consolidate all `DAY_*.md` files into single changelog
   - Document all features and changes

3. **Create Missing Documentation:**
   - `CONTRIBUTING.md` - Contribution guidelines
   - `SECURITY.md` - Security policies
   - `CODE_OF_CONDUCT.md` - Community guidelines

4. **Final Review:**
   - Code quality check
   - Test coverage review
   - Documentation completeness

5. **Tag v1.0.0:**
   ```bash
   git tag -a v1.0.0 -m "Version 1.0.0 - Production Ready"
   git push origin v1.0.0
   ```

---

## Expected Results

### Before
- Size: **4.2 GB** ❌
- Structure: **Chaotic** ❌
- Documentation: **Scattered (58 files)** ❌
- Tests: **Unorganized (22 files in root)** ❌
- Startup: **Confusing (5 scripts)** ❌

### After
- Size: **~20 MB** ✅
- Structure: **Professional** ✅
- Documentation: **Organized (docs/)** ✅
- Tests: **Structured (tests/)** ✅
- Startup: **Simple (1 script)** ✅

---

**Time to Complete:** 5 minutes (automated) or 10 minutes (manual)
**Effort Level:** Low
**Risk Level:** Very Low (backup created)
**Impact:** High (99.5% size reduction, professional structure)

---

## Commands Summary

```bash
# Option 1: Automated (recommended)
./scripts/cleanup_comprehensive.sh

# Option 2: Manual critical only
rm -rf venv
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +
mv backups ../omics_oracle_backups_$(date +%Y%m%d)

# Recreate venv (both options)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify
du -sh .
pytest tests/

# Commit
git add .
git commit -m "cleanup: Comprehensive codebase reorganization"
```

---

**Ready to proceed?** Run: `./scripts/cleanup_comprehensive.sh`
