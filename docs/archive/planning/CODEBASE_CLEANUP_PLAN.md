# OmicsOracle Codebase Cleanup Plan

## Current Issues
- Root directory is cluttered with temporary files, test files, and documentation
- Multiple environment files with unclear purposes
- Scattered debug and analysis scripts
- Inconsistent naming conventions
- Multiple testing frameworks and scripts

## Cleanup Strategy

### 1. Directory Structure Organization
```
OmicsOracle/
├── src/                          # Main source code (keep as is)
├── interfaces/                   # Interface modules (keep as is)
├── docs/                         # All documentation
├── tests/                        # All test files
├── scripts/                      # Utility and maintenance scripts
├── config/                       # Configuration files
├── data/                         # Data storage (keep as is)
├── logs/                         # Log files (keep as is)
├── .env files                    # Environment configurations
├── Docker files                  # Container configurations
├── pyproject.toml               # Python project config
├── requirements*.txt            # Dependencies
├── README.md                    # Main documentation
└── start.sh                     # Main startup script
```

### 2. Files to Move/Organize

#### Documentation Files (move to docs/)
- All *.md files except README.md
- Planning and status documents
- Reports and analysis documents

#### Test Files (move to tests/)
- All test_*.py files
- Testing scripts and frameworks
- Test reports and results

#### Utility Scripts (move to scripts/)
- Debug scripts
- Analysis scripts
- Validation scripts
- Monitoring scripts
- Maintenance scripts

#### Environment Files (consolidate)
- Keep only essential .env files
- Remove duplicates and obsolete configs

#### Temporary/Generated Files (remove)
- Log files (move to logs/)
- Cache files (already in cache/)
- Backup files (already in backups/)
- __pycache__ directories
- Temporary analysis files

### 3. Files to Remove
- Obsolete test and debug scripts
- Duplicate configuration files
- Temporary analysis files
- Generated log files in root

## Implementation Steps
1. Create proper directory structure
2. Move documentation files
3. Move test files
4. Move utility scripts
5. Consolidate environment files
6. Clean up temporary files
7. Update import paths if necessary
8. Test functionality after cleanup
