# OmicsOracle Code Quality & Linting Guide

## 🎯 Why Pre-Push Linting is Essential

**Running linting tests before pushing code is absolutely critical for several reasons:**

### 1. **Faster Feedback Loop**
- ⚡ **Local checks**: 5-30 seconds vs 2-5 minutes in CI/CD
- 🔧 **Immediate fixes**: Fix issues while code context is fresh in memory
- 🧠 **Context preservation**: No mental task-switching between commits

### 2. **CI/CD Efficiency**
- 💰 **Cost savings**: CI/CD resources are expensive (GitHub Actions minutes)
- 🚀 **Pipeline speed**: Don't waste time on preventable failures
- 👥 **Team productivity**: Don't block teammates with broken builds

### 3. **Code Quality**
- 🛡️ **Consistent standards**: Enforce coding standards automatically
- 🐛 **Early bug detection**: Catch issues before they reach production
- 📚 **Documentation**: Ensure code is well-documented and typed

## 🔧 Our Pre-Commit Setup

### Installed Hooks (`.pre-commit-config.yaml`)

```yaml
repos:
  # Basic file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - trailing-whitespace     # Remove trailing spaces
      - end-of-file-fixer      # Ensure files end with newline
      - check-yaml             # Validate YAML syntax
      - check-json             # Validate JSON syntax
      - check-merge-conflict   # Detect merge conflict markers
      - debug-statements       # Find forgotten debug statements

  # Code formatting
  - repo: https://github.com/psf/black
    hooks:
      - black                  # Python code formatter

  # Import sorting
  - repo: https://github.com/pycqa/isort
    hooks:
      - isort                  # Sort Python imports

  # Linting
  - repo: https://github.com/pycqa/flake8
    hooks:
      - flake8                 # Python linting

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - mypy                   # Static type checking

  # Security
  - repo: https://github.com/PyCQA/bandit
    hooks:
      - bandit                 # Security vulnerability scanning

  # ASCII enforcement (for CI/CD stability)
  - repo: local
    hooks:
      - ascii-only-enforcer    # Prevent Unicode issues in CI
```

## 🚀 Recommended Development Workflow

### 1. **Before Every Commit** (Automatic)
```bash
# These run automatically when you commit:
git add .
git commit -m "feat: add new feature"
# ↳ Pre-commit hooks run automatically here!
```

### 2. **Before Every Push** (Manual)
```bash
# Run comprehensive checks before pushing:
./scripts/pre_push_check.sh

# If all checks pass, then push:
git push origin feature-branch
```

### 3. **During Development** (As Needed)
```bash
# Run specific checks during development:
pre-commit run black --all-files           # Format code
pre-commit run flake8 --all-files          # Check linting
pre-commit run mypy --all-files            # Type checking
python -m pytest tests/unit/ -v            # Run tests
```

## 📋 Quick Reference Commands

### Setup (One-time)
```bash
pip install pre-commit
pre-commit install
```

### Daily Development
```bash
# Check specific files
pre-commit run --files src/omics_oracle/core/config.py

# Check all files
pre-commit run --all-files

# Skip hooks for emergency commits (use sparingly!)
git commit -m "emergency fix" --no-verify

# Update hook versions
pre-commit autoupdate
```

### Before Pushing
```bash
# Comprehensive pre-push check
./scripts/pre_push_check.sh

# Quick unit test check
python -m pytest tests/unit/ -v

# Security scan
python -m bandit -r src/
```

## 🛠️ IDE Integration

### VS Code Setup
Add to `.vscode/settings.json`:
```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### PyCharm Setup
1. **File → Settings → Tools → External Tools**
2. Add tools for Black, isort, flake8, mypy
3. **File → Settings → Editor → Code Style → Python**
4. Set line length to 88 (Black standard)

## 🎯 Quality Standards

### Code Quality Targets
- **Test Coverage**: >90% for core modules, >70% overall
- **Type Coverage**: 100% for public APIs
- **Security**: Zero high-severity vulnerabilities
- **Performance**: <5s response time, <2GB memory usage

### Enforcement Levels
- **Blocking**: Code formatting, syntax errors, import errors
- **Warning**: Type hints missing, security vulnerabilities
- **Advisory**: Code complexity, documentation coverage

## 🔥 Pro Tips

### 1. **Fast Development Cycle**
```bash
# Quick format and check cycle:
pre-commit run black isort flake8 --all-files && python -m pytest tests/unit/test_core.py -v
```

### 2. **Selective Hook Running**
```bash
# Run only specific hooks:
pre-commit run black                    # Just formatting
pre-commit run flake8 mypy             # Just linting + types
pre-commit run --all-files bandit      # Just security
```

### 3. **Emergency Bypasses** (Use Sparingly!)
```bash
# Skip all hooks for emergency commit:
git commit --no-verify -m "hotfix: critical bug"

# Skip specific hooks:
SKIP=flake8,mypy git commit -m "WIP: work in progress"
```

### 4. **Batch File Processing**
```bash
# Format specific directories:
black src/omics_oracle/core/
isort src/omics_oracle/core/

# Check specific file types:
find . -name "*.py" | xargs flake8
```

## 📊 Quality Metrics Dashboard

### Daily Metrics to Track
- Pre-commit hook success rate
- CI/CD pipeline failure rate due to quality issues
- Average time to fix quality issues
- Test coverage percentage
- Security vulnerability count

### Weekly Review Questions
1. Are developers bypassing hooks frequently?
2. Which quality checks fail most often?
3. How long does it take to fix quality issues?
4. Are CI/CD failures decreasing over time?

## 🚨 Common Issues & Solutions

### Issue: "Pre-commit hooks are too slow"
**Solution**:
```bash
# Run hooks in parallel (if supported):
pre-commit run --hook-stage manual --all-files

# Run only changed files during development:
pre-commit run
```

### Issue: "Hooks failing on CI but passing locally"
**Solution**:
```bash
# Ensure consistent environments:
pre-commit run --all-files --verbose
pre-commit clean && pre-commit install
```

### Issue: "Team members skipping hooks"
**Solution**:
- Set up branch protection rules requiring status checks
- Add quality gates to CI/CD pipeline
- Educate team on the importance and time savings

### Issue: "False positives in security scanning"
**Solution**:
```bash
# Create .bandit file to exclude false positives:
echo "[bandit]
exclude_dirs = tests/
skips = B101,B601" > .bandit
```

## 📚 Advanced Configuration

### Custom Hook for Genomics-Specific Checks
```yaml
- repo: local
  hooks:
    - id: genomics-terminology-check
      name: Check Genomics Terminology
      entry: python scripts/check_genomics_terms.py
      language: system
      files: \.(py|md)$
      description: Ensure consistent genomics terminology usage
```

### Performance Optimization
```yaml
- repo: https://github.com/psf/black
  rev: 23.9.1
  hooks:
    - id: black
      language_version: python3.11
      args: ["--line-length=88", "--fast"]  # Fast mode for development
```

## 🎉 Success Metrics

When properly implemented, you should see:
- **95%+ reduction** in CI/CD failures due to quality issues
- **80% faster** code review cycles
- **50% fewer** bugs reaching production
- **Consistent code style** across the entire team
- **Improved developer confidence** when making changes

---

## Quick Start Checklist

- [ ] `pre-commit install` (setup hooks)
- [ ] `chmod +x scripts/pre_push_check.sh` (make script executable)
- [ ] Test with `pre-commit run --all-files`
- [ ] Configure IDE for automatic formatting
- [ ] Run `./scripts/pre_push_check.sh` before every push
- [ ] Set up branch protection rules in GitHub
- [ ] Train team on the workflow

**Remember: The goal is to catch issues early and maintain high code quality without slowing down development!**
