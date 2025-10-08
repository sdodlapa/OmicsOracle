# ASCII-Only Enforcement Guide 🔒

**Version:** 1.0
**Date:** June 22, 2025
**Project:** OmicsOracle - ASCII Character Enforcement System

---

## 📋 Overview

OmicsOracle enforces strict ASCII-only characters (0x00-0x7F) in all code files, configurations, and scripts to ensure:
- **Cross-platform compatibility** across different operating systems
- **CI/CD pipeline reliability** without encoding issues
- **Terminal/shell compatibility** in diverse environments
- **Git workflow stability** with consistent character encoding

## 🎯 Policy Summary

### ✅ ASCII-Only Files (Enforced)
- **Python files** (`.py`)
- **Configuration files** (`.yml`, `.yaml`, `.json`, `.toml`, `.ini`, `.cfg`, `.conf`)
- **Shell scripts** (`.sh`, `.bash`, `.zsh`)
- **Web scripts** (`.js`, `.ts`, `.css`, `.xml`)
- **Build files** (`Dockerfile`, `Makefile`, `requirements*.txt`)
- **Database files** (`.sql`)

### 🌐 Unicode-Allowed Files (Web Interface)
- **HTML files** (`.html`, `.htm`) - Modern web interfaces legitimately use emojis and Unicode
- **Markdown files** (`.md`, `.rst`, `.tex`)
- **Documentation directories** (`docs/`, `README*`)
- **Research papers and PDFs** (extracted content)

### 📝 Unicode-Allowed Files (Documentation)
- **Markdown files** (`.md`, `.rst`, `.tex`)
- **Documentation directories** (`docs/`, `README*`)
- **Research papers and PDFs** (extracted content)

---

## 🔄 ASCII Character Replacements

### Status Symbols
| Unicode | ASCII Alternative | Use Case |
|---------|------------------|----------|
| ✅ | `[PASS]` or `[OK]` | Test results, success indicators |
| ❌ | `[FAIL]` or `[ERROR]` | Error states, failed tests |
| ⚠️ | `[WARN]` or `[WARNING]` | Warning messages |
| 🔧 | `[FIX]` or `[REPAIR]` | Fix suggestions |
| 🚀 | `[RUN]` or `[LAUNCH]` | Execution indicators |
| 📊 | `[DATA]` or `[STATS]` | Data processing |
| 🔍 | `[SEARCH]` or `[FIND]` | Search operations |
| 🎯 | `[TARGET]` or `[GOAL]` | Objectives, targets |

### Scientific Symbols
| Unicode | ASCII Alternative | Use Case |
|---------|------------------|----------|
| 🧬 | `[DNA]` or `[GENOMICS]` | Genomics references |
| 🔬 | `[LAB]` or `[SCIENCE]` | Scientific contexts |
| 🧪 | `[EXPERIMENT]` or `[TEST]` | Experimental work |
| 📈 | `[TREND_UP]` or `[INCREASE]` | Data trends |
| 📉 | `[TREND_DOWN]` or `[DECREASE]` | Data trends |
| 💻 | `[COMPUTER]` or `[SYSTEM]` | Computing references |

### Mathematical Symbols
| Unicode | ASCII Alternative | Use Case |
|---------|------------------|----------|
| ° | `deg` or `degrees` | Temperature, angles |
| ± | `+/-` or `plus_minus` | Uncertainty, ranges |
| × | `*` or `x` | Multiplication |
| ÷ | `/` | Division |
| ≤ | `<=` | Less than or equal |
| ≥ | `>=` | Greater than or equal |
| ≠ | `!=` | Not equal |
| ∞ | `inf` or `infinity` | Infinity |

### Greek Letters
| Unicode | ASCII Alternative | Use Case |
|---------|------------------|----------|
| α | `alpha` | Statistical parameters |
| β | `beta` | Coefficients |
| γ | `gamma` | Statistical distributions |
| δ | `delta` | Change/difference |
| ε | `epsilon` | Small values |
| λ | `lambda` | Wavelength, parameters |
| μ | `mu` or `micro` | Mean, micro units |
| π | `pi` | Mathematical constant |
| σ | `sigma` | Standard deviation |
| Ω | `omega` | Resistance units |

### Typography
| Unicode | ASCII Alternative | Use Case |
|---------|------------------|----------|
| " " | `" "` | Smart quotes → straight quotes |
| ' ' | `' '` | Smart quotes → straight quotes |
| – | `-` | En dash → hyphen |
| — | `--` | Em dash → double hyphen |
| … | `...` | Ellipsis → three dots |
| • | `*` or `-` | Bullet points |

---

## 🛠️ Enforcement System

### Automated Checking
The ASCII enforcer runs automatically via:

1. **Pre-commit Hooks**: Checks files before each commit
2. **CI/CD Pipeline**: Validates all files in pull requests
3. **Manual Execution**: Run `python scripts/ascii_enforcer.py` anytime

### Command Usage
```bash
# Check all files in current directory
python scripts/ascii_enforcer.py

# Check specific files
python scripts/ascii_enforcer.py src/omics_oracle/core/

# Verbose output
python scripts/ascii_enforcer.py -v

# Get help
python scripts/ascii_enforcer.py --help
```

### Pre-commit Integration
The ASCII enforcer is integrated into `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: ascii-only-enforcer
      name: ASCII-Only Character Enforcement
      entry: python scripts/ascii_enforcer.py
      language: system
      files: \.(py|yml|yaml|json|sh|bash|zsh|toml|ini|cfg|conf|txt|sql|js|ts|html|css|xml)$
      exclude: ^(docs/|\.md$|\.rst$|README)
      description: Enforce ASCII-only characters in all code and config files
```

---

## 🔍 Error Detection & Resolution

### Common Violations

#### 1. Smart Quotes in Strings
```python
# ❌ WRONG - Smart quotes
print("Hello World")

# ✅ CORRECT - Straight quotes
print("Hello World")
```

#### 2. Mathematical Symbols in Code
```python
# ❌ WRONG - Unicode symbols
temperature = 25°C
range_value = 10±2

# ✅ CORRECT - ASCII alternatives
temperature = "25degC"
range_value = "10+/-2"
```

#### 3. Status Emojis in Comments
```python
# ❌ WRONG - Emoji in comments
# ✅ This function works great!
# ❌ Fix this bug later

# ✅ CORRECT - ASCII alternatives
# [OK] This function works great!
# [TODO] Fix this bug later
```

#### 4. Greek Letters in Variable Names
```python
# ❌ WRONG - Greek letters
α = 0.05
β_coefficient = 1.23

# ✅ CORRECT - ASCII names
alpha = 0.05
beta_coefficient = 1.23
```

### Error Messages
The ASCII enforcer provides detailed error messages:

```
❌ Found 3 ASCII violations:
============================================================
FILE: src/omics_oracle/core/analyzer.py
LINE:   45 | COL:  12 | CRITICAL: Non-ASCII character '✅' (U+2705)
LINE:   67 | COL:   8 | PUNCTUATION: Non-ASCII character '"' (U+201C)
LINE:   89 | COL:  15 | EMOJI: Non-ASCII character '🧬' (U+1F9EC)
------------------------------------------------------------

💡 To fix ASCII violations:
   1. Replace non-ASCII characters with ASCII equivalents
   2. Move decorative content to markdown documentation
   3. Use ASCII art instead of Unicode symbols
   4. Replace smart quotes with straight quotes
```

---

## 📚 Best Practices

### 1. Code Comments
```python
# ✅ GOOD - ASCII status indicators
# [TODO] Implement error handling
# [FIXME] Memory leak in this function
# [NOTE] This algorithm is O(n log n)
# [WARNING] This function modifies global state

# ❌ AVOID - Unicode symbols in code
# 🔧 Implement error handling
# ⚠️ Memory leak in this function
```

### 2. Configuration Files
```yaml
# ✅ GOOD - ASCII configuration
status_indicators:
  success: "[PASS]"
  failure: "[FAIL]"
  warning: "[WARN]"

# ❌ AVOID - Unicode in config
status_indicators:
  success: "✅"
  failure: "❌"
  warning: "⚠️"
```

### 3. Log Messages
```python
# ✅ GOOD - ASCII log messages
logger.info("[SUCCESS] Data processing completed")
logger.error("[ERROR] Failed to connect to database")
logger.warning("[WARNING] API rate limit approaching")

# ❌ AVOID - Unicode in logs
logger.info("✅ Data processing completed")
logger.error("❌ Failed to connect to database")
logger.warning("⚠️ API rate limit approaching")
```

### 4. Test Assertions
```python
# ✅ GOOD - ASCII test messages
assert result == expected, "[FAIL] Expected genomics data parsing to succeed"
print("[PASS] All genomics tools integration tests passed")

# ❌ AVOID - Unicode in test output
assert result == expected, "❌ Expected genomics data parsing to succeed"
print("✅ All genomics tools integration tests passed")
```

---

## 🚨 Common Pitfalls

### 1. Copy-Paste from Documentation
- **Problem**: Copying code examples from markdown docs that contain Unicode
- **Solution**: Always check pasted code with ASCII enforcer before committing

### 2. IDE Auto-Completion
- **Problem**: Some IDEs insert smart quotes or Unicode symbols automatically
- **Solution**: Configure IDE to use straight quotes and ASCII-only characters

### 3. Scientific Notation
- **Problem**: Using Unicode Greek letters or mathematical symbols in code
- **Solution**: Use full ASCII names (`alpha`, `beta`, `sigma`, etc.)

### 4. Status Messages
- **Problem**: Using emoji for visual appeal in code or configs
- **Solution**: Use ASCII alternatives like `[OK]`, `[FAIL]`, `[WARN]`

---

## 🔧 IDE Configuration

### VS Code Settings
Add to your `settings.json`:
```json
{
  "editor.insertSpaces": true,
  "editor.tabSize": 4,
  "files.encoding": "utf8",
  "editor.rulers": [79],
  "python.defaultInterpreterPath": "./venv/bin/python",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Pre-commit Setup
Install pre-commit hooks:
```bash
# Install pre-commit
pip install pre-commit

# Install hooks for the repository
pre-commit install

# Run on all files (optional)
pre-commit run --all-files
```

---

## 📊 Monitoring & Metrics

### Quality Gates
- **Zero tolerance**: No ASCII violations allowed in main branch
- **Pre-commit blocking**: Commits with violations are rejected
- **CI/CD enforcement**: Pull requests with violations cannot merge
- **Regular audits**: Weekly scans of entire codebase

### Reporting
The ASCII enforcer provides detailed metrics:
- Total files scanned
- Number of violations found
- Types of violations (emoji, punctuation, mathematical symbols)
- Files with most violations
- Compliance percentage

---

## 🌟 Benefits

### Technical Benefits
- **Consistent encoding**: No character encoding issues across platforms
- **Terminal compatibility**: Works in all terminal environments
- **Git reliability**: No merge conflicts due to character encoding
- **CI/CD stability**: Prevents pipeline failures from encoding issues

### Development Benefits
- **Code clarity**: ASCII alternatives are often more descriptive
- **Searchability**: ASCII text is easily searchable and greppable
- **Documentation**: Forces clear communication without relying on symbols
- **Internationalization**: ASCII works in all locales and languages

### Scientific Benefits
- **Reproducibility**: Code runs consistently across all environments
- **Collaboration**: Works for international teams with different systems
- **Archival**: ASCII ensures long-term readability and accessibility
- **Standards compliance**: Follows scientific computing best practices

---

## 📞 Support & Troubleshooting

### Getting Help
1. **Check this guide** for common replacements and solutions
2. **Run ASCII enforcer** with `-v` flag for detailed output
3. **Review error messages** for specific character codes and locations
4. **Consult team** for domain-specific ASCII alternatives

### Common Questions

**Q: Can I use Unicode in documentation?**
A: Yes! Unicode is allowed and encouraged in `.md`, `.rst`, and `docs/` files.

**Q: What about scientific notation like α = 0.05?**
A: Use `alpha = 0.05` in code, but `α = 0.05` is fine in markdown docs.

**Q: How do I handle existing violations?**
A: Run the ASCII enforcer to identify violations, then replace them using the tables in this guide.

**Q: What if I need a symbol not in the replacement table?**
A: Create a descriptive ASCII alternative and document it for team consistency.

---

## 🎯 Conclusion

The ASCII-only policy ensures OmicsOracle remains a robust, reliable, and portable scientific tool. By following these guidelines and using the automated enforcement system, we maintain code quality while preserving the visual appeal of our documentation.

**Remember**: ASCII in code, Unicode in docs – that's the OmicsOracle way! 🚀

---

*This guide is living documentation. Update it as new ASCII alternatives are discovered and adopted by the team.*
