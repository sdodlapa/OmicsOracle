# 🧹 Phase 0: Comprehensive Cleanup Plan

**Phase**: 0 of 4
**Duration**: 2 weeks (10 working days)
**Effort**: ~40 hours
**Start**: Immediately after planning approval
**Goal**: Clean workspace, fix critical organizational issues

---

## 📋 Phase Overview

This phase focuses on removing technical debt and organizational issues that block future development. The goal is to create a clean foundation for the multi-agent architecture.

**Key Principle**: Delete ruthlessly, fix systematically, document clearly.

---

## 🎯 Objectives

1. **Remove Backup Bloat**: Delete 365MB of duplicate code
2. **Fix Import Structure**: Eliminate all sys.path manipulations
3. **Consolidate Routes**: Merge 7 route files into 3
4. **Clean Package Structure**: Add missing __init__.py files
5. **Organize Tests**: Restructure test directory
6. **Update Documentation**: Sync docs with reality

---

## 📅 Timeline

### Week 1: Emergency Cleanup
- **Day 1-2**: Backup removal and git cleanup
- **Day 3-4**: Import structure fixes
- **Day 5**: Route consolidation

### Week 2: Structure and Quality
- **Day 6-7**: Package structure improvements
- **Day 8**: Test organization
- **Day 9**: Documentation updates
- **Day 10**: Final review and validation

---

## 🔨 Detailed Tasks

### Task 1: Remove Backup Directory (Day 1-2)
**Duration**: 4 hours
**Priority**: CRITICAL

#### Subtasks
1. **Audit backup content** (1 hour)
   ```bash
   # Document what's in backups/
   find backups/ -name "*.py" -type f | wc -l
   find backups/ -name "main.py" -type f
   du -sh backups/

   # Create inventory
   tree backups/ -L 3 > docs/cleanup/backup_inventory.txt
   ```

2. **Create git tag for reference** (0.5 hours)
   ```bash
   # Tag current state before deletion
   git tag -a v1-before-cleanup -m "State before backup cleanup - Oct 2025"
   git tag -a v1-legacy-backups -m "Reference point for backup code"
   ```

3. **Remove backup directory** (0.5 hours)
   ```bash
   # Delete backups/
   git rm -r backups/
   git commit -m "cleanup: Remove 365MB backup directory

   - Removed duplicate code in backups/ directory
   - Tagged as v1-legacy-backups for reference
   - Reduces repository size by 70%
   - All code preserved in git history"
   ```

4. **Verify and push** (1 hour)
   ```bash
   # Verify repository size
   du -sh .

   # Verify no broken imports
   python -m pytest tests/ -k "test_import"

   # Push changes
   git push origin main
   git push origin v1-before-cleanup v1-legacy-backups
   ```

5. **Update .gitignore** (1 hour)
   ```bash
   # Add to .gitignore
   echo "backups/" >> .gitignore
   echo "*.bak" >> .gitignore
   echo "*_backup/" >> .gitignore
   git add .gitignore
   git commit -m "cleanup: Update .gitignore to prevent future backup bloat"
   ```

**Success Criteria**:
- [ ] backups/ directory removed
- [ ] Repository size < 50MB
- [ ] Git tags created for reference
- [ ] No broken imports
- [ ] Changes pushed to remote

**Deliverables**:
- Clean repository without backups/
- backup_inventory.txt for reference
- Git tags for code archaeology

---

### Task 2: Fix Import Structure (Day 3-4)
**Duration**: 8 hours
**Priority**: CRITICAL

#### Subtasks

1. **Audit sys.path usage** (1 hour)
   ```bash
   # Find all sys.path manipulations
   grep -r "sys.path" . --include="*.py" --exclude-dir=".venv" > docs/cleanup/syspath_audit.txt

   # Count occurrences
   grep -r "sys.path.insert" . --include="*.py" --exclude-dir=".venv" | wc -l
   ```

2. **Add missing __init__.py files** (1 hour)
   ```bash
   # Find directories without __init__.py
   find src -type d -not -path "*/.*" -not -path "*/__pycache__" \
     -exec bash -c '[ ! -f {}/__init__.py ] && echo {}' \;

   # Add __init__.py to all package directories
   find src/omics_oracle -type d -not -path "*/.*" \
     -not -path "*/__pycache__" \
     -not -path "*.egg-info" \
     -exec touch {}/__init__.py \;
   ```

3. **Fix imports in production code** (3 hours)
   ```bash
   # Run the existing fix_imports.py script
   python scripts/debug/fix_imports.py --analyze
   python scripts/debug/fix_imports.py --fix --target src/

   # Manual fixes for complex cases
   # Edit files with relative imports
   ```

4. **Update pyproject.toml** (1 hour)
   ```toml
   # Ensure proper package configuration
   [tool.setuptools]
   packages = {find = {where = ["src"], include = ["omics_oracle*"]}}

   [tool.setuptools.package-data]
   omics_oracle = ["py.typed"]
   ```

5. **Test pip installation** (1 hour)
   ```bash
   # Create fresh virtual environment
   python -m venv test_venv
   source test_venv/bin/activate

   # Try editable install
   pip install -e .

   # Test imports
   python -c "from omics_oracle.pipeline import OmicsOracle; print('Success')"
   python -c "from omics_oracle.nlp import BiomedicalNER; print('Success')"
   python -c "from omics_oracle.geo_tools import UnifiedGEOClient; print('Success')"

   deactivate
   rm -rf test_venv
   ```

6. **Fix script imports** (1 hour)
   ```bash
   # Update scripts to use installed package
   # No more sys.path hacks in scripts/
   ```

**Success Criteria**:
- [ ] Zero sys.path manipulations in src/
- [ ] All packages have __init__.py
- [ ] pip install -e . works
- [ ] All imports work without sys.path
- [ ] Scripts use proper imports

**Deliverables**:
- syspath_audit.txt documenting changes
- Clean import structure
- Working pip installation

---

### Task 3: Consolidate Routes (Day 5)
**Duration**: 4 hours
**Priority**: HIGH

#### Current State
```
routes/
├── __init__.py          (202 lines) - Too much logic
├── analysis.py          (156 lines)
├── enhanced_search.py   (96 lines)
├── futuristic_search.py (225 lines)
├── health.py            (21 lines)
├── search.py            (13 lines) - Stub
├── v1.py                (13 lines) - Stub
└── v2.py                (13 lines) - Stub
```

#### Target State
```
routes/
├── __init__.py          (50 lines) - Route setup only
├── search.py            (300 lines) - All search endpoints
├── analysis.py          (156 lines) - Keep as-is
└── health.py            (21 lines) - Keep as-is
```

#### Subtasks

1. **Analyze route dependencies** (1 hour)
   ```bash
   # Map out route dependencies
   grep -r "include_router" src/omics_oracle/presentation/web/routes/
   ```

2. **Merge search routes** (2 hours)
   ```python
   # Create new unified search.py
   # Merge: enhanced_search.py + futuristic_search.py + v1.py + v2.py
   # Organize by API version

   # Structure:
   # - /api/v1/search/* endpoints
   # - /api/v2/search/* endpoints
   # - Clear versioning strategy
   ```

3. **Update __init__.py** (0.5 hours)
   ```python
   # Simplify to route setup only
   # Remove dashboard logic (move to separate file if needed)
   ```

4. **Test consolidated routes** (0.5 hours)
   ```bash
   # Start server
   uvicorn omics_oracle.presentation.web.main:app --reload

   # Test endpoints
   curl http://localhost:8000/health
   curl http://localhost:8000/api/v2/search/enhanced?query=test
   ```

**Success Criteria**:
- [ ] 7 route files → 4 route files
- [ ] All endpoints still functional
- [ ] Clear API versioning
- [ ] __init__.py simplified

**Deliverables**:
- Consolidated search.py
- Simplified __init__.py
- Route migration guide

---

### Task 4: Package Structure Improvements (Day 6-7)
**Duration**: 8 hours
**Priority**: MEDIUM

#### Subtasks

1. **Create py.typed marker** (0.5 hours)
   ```bash
   touch src/omics_oracle/py.typed
   git add src/omics_oracle/py.typed
   git commit -m "feat: Add py.typed marker for type checking support"
   ```

2. **Add __all__ exports** (3 hours)
   ```python
   # Add to each __init__.py
   # Example: src/omics_oracle/core/__init__.py

   """
   Core infrastructure for OmicsOracle.

   Exports:
       Config: Configuration management
       OmicsOracleException: Base exception class
   """

   from .config import Config
   from .exceptions import OmicsOracleException

   __all__ = ["Config", "OmicsOracleException"]
   ```

3. **Organize imports** (2 hours)
   ```bash
   # Run isort on all files
   isort src/ tests/ scripts/
   ```

4. **Add module docstrings** (2 hours)
   ```python
   # Add to each module
   """
   Module purpose and description.

   This module provides...
   """
   ```

5. **Verify structure** (0.5 hours)
   ```bash
   # Check package structure
   python -c "import omics_oracle; print(dir(omics_oracle))"
   ```

**Success Criteria**:
- [ ] All packages have proper __init__.py with __all__
- [ ] py.typed marker added
- [ ] Imports organized with isort
- [ ] Module docstrings added

**Deliverables**:
- Well-structured Python package
- Type checking support
- Clear public API

---

### Task 5: Test Organization (Day 8)
**Duration**: 4 hours
**Priority**: MEDIUM

#### Current State
```
tests/
├── 88 test files (scattered)
└── Various naming conventions
```

#### Target State
```
tests/
├── unit/
│   ├── core/
│   ├── services/
│   ├── pipeline/
│   └── nlp/
├── integration/
│   ├── api/
│   └── pipeline/
├── conftest.py
└── README.md
```

#### Subtasks

1. **Create test directory structure** (0.5 hours)
   ```bash
   mkdir -p tests/unit/{core,services,pipeline,nlp,geo_tools}
   mkdir -p tests/integration/{api,pipeline}
   ```

2. **Move existing tests** (2 hours)
   ```bash
   # Categorize and move tests
   # Unit tests → tests/unit/
   # Integration tests → tests/integration/
   ```

3. **Create conftest.py** (1 hour)
   ```python
   # Add common fixtures
   import pytest
   from omics_oracle.core.config import Config

   @pytest.fixture
   def test_config():
       """Provide test configuration."""
       return Config()
   ```

4. **Add test README** (0.5 hours)
   ```markdown
   # OmicsOracle Tests

   ## Structure
   - unit/: Unit tests for individual components
   - integration/: Integration tests for system components

   ## Running Tests
   pytest tests/unit/  # Unit tests only
   pytest tests/integration/  # Integration tests
   pytest  # All tests
   ```

**Success Criteria**:
- [ ] Tests organized by type
- [ ] Clear directory structure
- [ ] Shared fixtures in conftest.py
- [ ] Test documentation

**Deliverables**:
- Organized test structure
- Common test fixtures
- Test README

---

### Task 6: Documentation Updates (Day 9)
**Duration**: 4 hours
**Priority**: MEDIUM

#### Subtasks

1. **Update README.md** (1 hour)
   ```markdown
   # Add cleanup status
   # Update installation instructions
   # Add architecture overview link
   ```

2. **Create cleanup summary** (1 hour)
   ```markdown
   # docs/cleanup/CLEANUP_SUMMARY.md

   ## What Was Done
   - Removed 365MB backup directory
   - Fixed 50+ sys.path manipulations
   - Consolidated 7 route files → 4
   - Organized test structure

   ## Before/After Metrics
   - Repository size: 400MB → 50MB
   - Import violations: 50+ → 0
   - Route files: 7 → 4
   - Test organization: Scattered → Structured
   ```

3. **Update architecture docs** (1 hour)
   ```markdown
   # Update ARCHITECTURE.md with cleanup changes
   ```

4. **Document decisions** (1 hour)
   ```markdown
   # docs/decisions/CLEANUP_DECISIONS.md

   ## Why We Removed Backups
   ## Why We Chose This Import Strategy
   ## Why We Consolidated Routes This Way
   ```

**Success Criteria**:
- [ ] README updated
- [ ] Cleanup documented
- [ ] Decisions recorded
- [ ] Architecture docs current

**Deliverables**:
- Updated documentation
- Cleanup summary
- Decision records

---

### Task 7: Final Review and Validation (Day 10)
**Duration**: 4 hours
**Priority**: CRITICAL

#### Subtasks

1. **Run all tests** (1 hour)
   ```bash
   pytest -v
   pytest --cov=src/omics_oracle
   ```

2. **Verify installation** (1 hour)
   ```bash
   pip install -e .
   python -m omics_oracle.pipeline --version
   ```

3. **Check code quality** (1 hour)
   ```bash
   black --check src/
   flake8 src/
   mypy src/
   ```

4. **Review changes** (1 hour)
   ```bash
   git log --oneline --since="2 weeks ago"
   git diff v1-before-cleanup..HEAD --stat
   ```

**Success Criteria**:
- [ ] All tests passing
- [ ] Code quality checks pass
- [ ] Installation works
- [ ] Changes reviewed

**Deliverables**:
- Test report
- Quality check results
- Phase 0 completion report

---

## 📊 Success Metrics

### Quantitative Metrics
- [ ] Repository size: 400MB → <50MB (87% reduction)
- [ ] sys.path violations: 50+ → 0 (100% elimination)
- [ ] Route files: 7 → 4 (43% consolidation)
- [ ] Test organization: 0 → 100% (clear structure)
- [ ] Import success rate: Variable → 100%

### Qualitative Metrics
- [ ] pip install -e . works without issues
- [ ] All imports work without sys.path hacks
- [ ] Code passes pre-commit hooks
- [ ] Documentation reflects reality
- [ ] Clean git history

---

## 🚨 Risks and Mitigation

### Risk 1: Breaking Changes During Cleanup
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Create git tags before major changes
- Run tests after each task
- Keep v1 code intact until verified

### Risk 2: Import Fixes Break Dependencies
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Test imports incrementally
- Use automated script where possible
- Manual review of complex cases

### Risk 3: Route Consolidation Breaks Frontend
**Probability**: Low
**Impact**: High
**Mitigation**:
- Test all endpoints before/after
- Update frontend references
- Keep old routes temporarily if needed

---

## 📝 Checklist

### Pre-Phase Checklist
- [ ] Master plan approved
- [ ] Phase 0 plan reviewed
- [ ] Development environment ready
- [ ] Git repository clean
- [ ] Backup of current state

### Daily Checklist
- [ ] Review tasks for the day
- [ ] Run tests before starting
- [ ] Commit frequently
- [ ] Document changes
- [ ] Run tests before ending

### End of Phase Checklist
- [ ] All tasks completed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changes committed and pushed
- [ ] Phase 0 report written
- [ ] Phase 1 planning started

---

## 📋 Command Reference

### Quick Commands
```bash
# Remove backups
git rm -r backups/ && git commit -m "cleanup: Remove backup directory"

# Fix imports
python scripts/debug/fix_imports.py --fix --target src/

# Run tests
pytest -v tests/

# Check code quality
black src/ && isort src/ && flake8 src/

# Verify installation
pip install -e . && python -c "from omics_oracle.pipeline import OmicsOracle"
```

---

## 📊 Progress Tracking

### Daily Progress Log

**Day 1**: ___________
- [ ] Task 1.1: Backup audit
- [ ] Task 1.2: Git tags

**Day 2**: ___________
- [ ] Task 1.3: Remove backups
- [ ] Task 1.4: Verify and push

**Day 3**: ___________
- [ ] Task 2.1: Audit sys.path
- [ ] Task 2.2: Add __init__.py files

**Day 4**: ___________
- [ ] Task 2.3: Fix imports
- [ ] Task 2.4: Update pyproject.toml

**Day 5**: ___________
- [ ] Task 3: Consolidate routes

**Day 6**: ___________
- [ ] Task 4.1-4.3: Package structure

**Day 7**: ___________
- [ ] Task 4.4-4.5: Complete package structure

**Day 8**: ___________
- [ ] Task 5: Test organization

**Day 9**: ___________
- [ ] Task 6: Documentation

**Day 10**: ___________
- [ ] Task 7: Final review

---

## 🎯 Deliverables Summary

1. **Clean Repository**: <50MB, no backups/
2. **Fixed Imports**: Zero sys.path hacks, proper package structure
3. **Consolidated Routes**: 4 files instead of 7
4. **Organized Tests**: Clear unit/integration structure
5. **Updated Documentation**: Reflects all changes
6. **Quality Report**: Test and code quality results
7. **Completion Report**: Phase 0 summary and metrics

---

**Phase Status**: READY TO START
**Next Phase**: Phase 1 - Algorithm Extraction
**Estimated Start Date**: After Phase 0 completion (Week 3)

---

**Document Version**: 1.0
**Last Updated**: October 2, 2025
**Owner**: Development Team
