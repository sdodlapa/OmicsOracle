# OmicsOracle Codebase Cleanup Plan 🧹

**Date:** June 22, 2025
**Priority:** High - Maintain Clean, Professional Codebase

## 🎯 Cleanup Goals

1. **Eliminate redundancy** - Remove duplicate and outdated files
2. **Improve organization** - Clear directory structure
3. **Reduce cognitive load** - Fewer files, clearer purpose
4. **Maintain quality** - Keep essential documentation and code

## 📁 Files to Remove/Consolidate

### Immediate Removal (Low Risk)
```bash
# Backup files - no longer needed
scripts/ascii_enforcer_backup.py

# Cache directories - regenerated automatically
.mypy_cache/
.pytest_cache/
src/.mypy_cache/
scripts/.mypy_cache/
tests/.mypy_cache/
```

### Documentation Consolidation

#### Summary Files to Merge/Remove:
1. **PROJECT_SETUP_SUMMARY.md** → Merge into README.md
2. **DEVELOPMENT_PLAN_UPDATE_SUMMARY.md** → Archive or remove (outdated)
3. **ASCII_ENFORCEMENT_IMPLEMENTATION_SUMMARY.md** → Archive (completed feature)
4. **DEVELOPMENT_PLAN_QUALITY_UPDATE.md** → Archive (superseded)
5. **PHASE_1_IMPLEMENTATION_CHECKLIST.md** → Archive (completed)
6. **workflow_monitor_enhancement_plan.md** → Move to docs/

#### Action Plan:
- Keep **DEVELOPMENT_PLAN.md** as the single source of truth
- Keep **README.md** as the main entry point
- Keep **CORE_PHILOSOPHY.md** for team principles
- Archive completed implementation summaries to `docs/archive/`

### Resource Files to Relocate

#### Move PDFs to `data/references/`:
```bash
mkdir -p data/references/
mv "Data System Architecture Overview.pdf" data/references/
mv "Tools and Libraries for GEO Metadata Access.pdf" data/references/
mv "Naming Suggestions for a GEO Metadata Summarization Tool.pdf" data/references/
```

#### Extract docs folder consolidation:
```bash
# Move extracted content to docs/references/
mv extracted_docs/ docs/references/extracted_pdfs/
```

## 🔧 Recommended File Structure (After Cleanup)

```
OmicsOracle/
├── README.md                           # Main entry point
├── DEVELOPMENT_PLAN.md                 # Single source roadmap
├── CORE_PHILOSOPHY.md                  # Team principles
├── pyproject.toml                      # Package config
├── requirements*.txt                   # Dependencies
├── docker-compose.yml                  # Dev environment
├── Makefile                           # Build automation
├── .pre-commit-config.yaml            # Quality gates
├── .github/                           # CI/CD workflows
├── src/omics_oracle/                  # Source code
├── tests/                             # Test suite
├── scripts/                           # Utility scripts
├── docs/                              # Living documentation
│   ├── CODE_QUALITY_GUIDE.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── archive/                       # Completed summaries
│   └── references/                    # Reference materials
├── data/
│   ├── references/                    # PDFs, external docs
│   ├── examples/                      # Sample data
│   └── test_data/                     # Test fixtures
└── deployment/                       # Docker, K8s configs
```

## ⚡ Quick Cleanup Script

```bash
#!/bin/bash
# OmicsOracle Cleanup Script

echo "🧹 Starting OmicsOracle codebase cleanup..."

# 1. Remove backup files
rm -f scripts/ascii_enforcer_backup.py

# 2. Create archive directory
mkdir -p docs/archive

# 3. Move completed summaries to archive
mv PROJECT_SETUP_SUMMARY.md docs/archive/
mv DEVELOPMENT_PLAN_UPDATE_SUMMARY.md docs/archive/
mv ASCII_ENFORCEMENT_IMPLEMENTATION_SUMMARY.md docs/archive/
mv DEVELOPMENT_PLAN_QUALITY_UPDATE.md docs/archive/
mv PHASE_1_IMPLEMENTATION_CHECKLIST.md docs/archive/
mv workflow_monitor_enhancement_plan.md docs/archive/

# 4. Create references directory
mkdir -p data/references

# 5. Move PDFs to references
mv "Data System Architecture Overview.pdf" data/references/
mv "Tools and Libraries for GEO Metadata Access.pdf" data/references/
mv "Naming Suggestions for a GEO Metadata Summarization Tool.pdf" data/references/

# 6. Move extracted docs
mkdir -p docs/references
mv extracted_docs docs/references/extracted_pdfs

# 7. Clean cache directories (they'll regenerate)
rm -rf .mypy_cache .pytest_cache
find . -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

echo "✅ Cleanup complete! Codebase is now organized and clutter-free."
echo "📁 Files moved to docs/archive/ and data/references/"
echo "🔄 Don't forget to update .gitignore for cache directories"
```

## 📊 Expected Results

### Before Cleanup:
- 37 markdown files
- PDFs scattered in root
- Multiple redundant summaries
- Backup files taking space

### After Cleanup:
- ~15 essential markdown files
- Organized reference materials
- Single source of truth docs
- Clean project root

## 🚀 Implementation Priority

**Phase 1 (Immediate - 15 minutes):**
1. Run cleanup script
2. Update .gitignore for cache dirs
3. Update README.md links if needed

**Phase 2 (Next session - 30 minutes):**
1. Review archived files
2. Update internal documentation links
3. Verify all references still work

## ✅ Quality Checklist

- [ ] No broken internal links after cleanup
- [ ] Essential documentation preserved
- [ ] Reference materials accessible
- [ ] Build/test processes unaffected
- [ ] Team can find what they need easily

---

**Next Steps:** Review this plan, then execute cleanup script to maintain a professional, organized codebase.
