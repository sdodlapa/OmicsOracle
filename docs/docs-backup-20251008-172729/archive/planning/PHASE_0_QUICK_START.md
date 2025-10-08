# 🚀 Phase 0 Quick Start Guide

**Start Date**: October 2, 2025
**Duration**: 2 weeks
**Status**: READY TO BEGIN

---

## 📋 Prerequisites

Before starting Phase 0, ensure:
- [ ] You have read the Master Plan
- [ ] You have read the Phase 0 Cleanup Plan
- [ ] You have a clean working directory
- [ ] You have committed all current changes
- [ ] Your development environment is set up

---

## 🎯 Today's Action: Begin Phase 0 Cleanup

### Step 1: Create Cleanup Branch
```bash
cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle
git checkout -b cleanup-phase-0
```

### Step 2: Start with Task 1 - Backup Removal

#### Quick Command Sequence
```bash
# 1. Document what's in backups
find backups/ -name "*.py" -type f | wc -l
du -sh backups/
tree backups/ -L 2 > docs/cleanup/backup_inventory.txt

# 2. Create git tag for reference
git tag -a v1-before-cleanup -m "State before Phase 0 cleanup - Oct 2025"
git tag -a v1-legacy-backups -m "Reference for backup code if needed"

# 3. Remove backups directory
git rm -r backups/
git commit -m "cleanup: Remove 365MB backup directory

Phase 0, Task 1: Backup removal
- Deleted backups/ directory (365MB of duplicates)
- Tagged as v1-legacy-backups for reference
- All code preserved in git history
- Reduces repository size by 70%"

# 4. Update .gitignore
cat >> .gitignore << EOF

# Prevent future backup bloat
backups/
*.bak
*_backup/
*_old/
EOF

git add .gitignore
git commit -m "cleanup: Update .gitignore to prevent backup bloat"

# 5. Verify
du -sh .
git log --oneline -5
```

### Step 3: Test Everything Still Works
```bash
# Run tests
pytest tests/ -v

# Verify no broken imports
python -c "from omics_oracle.pipeline import OmicsOracle; print('✓ Pipeline imports')"
python -c "from omics_oracle.nlp import BiomedicalNER; print('✓ NLP imports')"
python -c "from omics_oracle.geo_tools import UnifiedGEOClient; print('✓ GEO imports')"
```

### Step 4: Push Changes
```bash
git push origin cleanup-phase-0
git push origin v1-before-cleanup v1-legacy-backups
```

---

## 📊 Task 1 Success Criteria

After completing Task 1, you should have:
- [ ] backups/ directory removed from repository
- [ ] Repository size reduced to <50MB
- [ ] Git tags created (v1-before-cleanup, v1-legacy-backups)
- [ ] .gitignore updated to prevent future backups
- [ ] All tests still passing
- [ ] No broken imports
- [ ] Changes committed and pushed

---

## 🔄 What's Next?

After completing Task 1 (Day 1-2), proceed to:
- **Task 2**: Fix Import Structure (Day 3-4)
- **Task 3**: Consolidate Routes (Day 5)
- **Task 4**: Package Structure (Day 6-7)
- **Task 5**: Test Organization (Day 8)
- **Task 6**: Documentation (Day 9)
- **Task 7**: Final Review (Day 10)

---

## 📝 Daily Log

Keep track of your progress:

**Day 1**: ___________
- Started Phase 0
- Removed backups/ directory
- Created git tags
- Status: ___________

**Day 2**: ___________
- Verified changes
- Pushed to remote
- Status: ___________

---

## 🆘 If Something Goes Wrong

### Broken Imports?
```bash
# Restore from tag
git checkout v1-before-cleanup
git checkout -b cleanup-phase-0-retry
```

### Need Backup Code?
```bash
# Access old code
git checkout v1-legacy-backups -- backups/specific_file.py
# Review and extract what you need
# Then clean up again
```

### Tests Failing?
```bash
# Check what broke
git diff v1-before-cleanup..HEAD

# Revert specific files if needed
git checkout v1-before-cleanup -- path/to/file.py
```

---

## ✅ Completion Checklist

Before moving to Task 2:
- [ ] Task 1 completed
- [ ] All success criteria met
- [ ] Tests passing
- [ ] Changes committed
- [ ] Changes pushed
- [ ] Documentation updated

---

## 📞 Questions?

Refer to:
- Master Plan: `docs/planning/MASTER_PLAN.md`
- Phase 0 Plan: `docs/planning/PHASE_0_CLEANUP_PLAN.md`
- Architecture Evaluation: `docs/architecture/COMPREHENSIVE_CODEBASE_EVALUATION.md`

---

**Ready to begin!** 🚀

Execute the commands above to start Phase 0, Task 1.
