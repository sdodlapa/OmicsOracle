# Import Structure Fix Plan

## Immediate Actions Required

### 1. Remove all sys.path manipulations
```bash
# Find and remove all instances
grep -r "sys.path" src/ --include="*.py"
# Replace with proper relative imports
```

### 2. Create missing __init__.py files
```bash
find src/ -type d -exec touch {}/__init__.py \;
```

### 3. Fix relative imports
```python
# BEFORE (problematic)
sys.path.insert(0, str(project_root))
from src.omics_oracle.core.config import Config

# AFTER (correct)
from ...core.config import Config
```

### 4. Update pyproject.toml for proper packaging
```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "omics-oracle"
# ... existing config

[tool.setuptools.packages.find]
where = ["src"]
include = ["omics_oracle*"]
```

## Implementation Script
A script exists at `scripts/debug/fix_imports.py` that can automate this process.
