# OmicsOracle Codebase Cleanup Plan

## Overview

Before conducting the data integrity investigation, we need to perform a comprehensive cleanup of the codebase to:
1. Remove all remaining mock/sample/fallback data
2. Eliminate data corruption sources
3. Improve code clarity and maintainability
4. Establish clear data flow patterns
5. Implement proper error handling and validation

## Phase 1: Mock Data and Fallback Elimination

### 1.1 Complete Mock Data Removal
- [ ] Search and remove ALL references to mock, sample, dummy, placeholder data
- [ ] Remove any hardcoded test data or fallback content
- [ ] Eliminate any data generation or simulation code
- [ ] Remove development-only data sources

### 1.2 Fallback Logic Elimination
- [ ] Remove all fallback mechanisms that could mix real and fake data
- [ ] Eliminate default/placeholder content generation
- [ ] Remove any "safe" fallback data that could mask real errors
- [ ] Ensure all errors are properly surfaced

### 1.3 Cache and Storage Cleanup
- [ ] Clear all cached data that might contain mixed/corrupted content
- [ ] Reset any persistent storage with potentially invalid data
- [ ] Remove any development artifacts or test data
- [ ] Clean up any temporary data files

## Phase 2: Data Flow Standardization

### 2.1 API Response Standardization
- [ ] Standardize all API response formats
- [ ] Implement consistent error response structures
- [ ] Remove any response transformation that could corrupt data
- [ ] Ensure all data sources are clearly identified

### 2.2 Data Processing Pipeline Cleanup
- [ ] Simplify data transformation logic
- [ ] Remove unnecessary data processing steps
- [ ] Eliminate any data merging that could cause cross-contamination
- [ ] Implement clear data provenance tracking

### 2.3 Frontend Data Handling
- [ ] Clean up frontend data processing logic
- [ ] Remove any client-side data generation or modification
- [ ] Ensure all displayed data comes directly from backend
- [ ] Implement proper error handling for missing data

## Phase 3: Code Organization and Documentation

### 3.1 File Structure Cleanup
- [ ] Remove unused files and modules
- [ ] Organize code into clear functional areas
- [ ] Remove duplicate or redundant code
- [ ] Clean up import statements and dependencies

### 3.2 Function and Class Cleanup
- [ ] Remove unused functions and methods
- [ ] Simplify complex functions
- [ ] Eliminate redundant code paths
- [ ] Improve function naming and documentation

### 3.3 Configuration Cleanup
- [ ] Remove development/testing configurations
- [ ] Standardize configuration management
- [ ] Remove hardcoded values and magic numbers
- [ ] Document all configuration options

## Phase 4: Error Handling and Validation

### 4.1 Input Validation
- [ ] Implement comprehensive input validation
- [ ] Add data type and format checking
- [ ] Validate all external API responses
- [ ] Implement proper sanitization

### 4.2 Error Handling Standardization
- [ ] Implement consistent error handling patterns
- [ ] Remove error suppression that could hide issues
- [ ] Add proper logging for all error conditions
- [ ] Ensure errors are properly propagated

### 4.3 Data Integrity Checks
- [ ] Add validation for all data transformations
- [ ] Implement consistency checks between related data
- [ ] Add verification against authoritative sources
- [ ] Create data quality metrics

## Specific Files to Clean Up

### Backend Files
```
interfaces/futuristic/main.py
- Remove any remaining mock data references
- Clean up error handling
- Standardize response formats
- Add data validation

src/omics_oracle/geo_tools/client.py
- Verify data extraction accuracy
- Clean up metadata processing
- Add response validation
- Remove any fallback logic

src/omics_oracle/geo_tools/geo_client.py
- Clean up GEO API interaction
- Standardize data mapping
- Add error handling
- Remove development artifacts

pipeline_monitor.py
- Remove any diagnostic data generation
- Clean up reporting logic
- Standardize output formats
- Add validation checks
```

### Frontend Files
```
interfaces/futuristic/static/js/main_clean.js
- Remove any client-side data generation
- Clean up data processing logic
- Standardize error handling
- Remove development/debugging code

interfaces/futuristic/templates/index.html
- Remove any hardcoded content
- Clean up form validation
- Standardize UI elements
- Remove development artifacts
```

### Configuration Files
```
requirements.txt / pyproject.toml
- Remove unused dependencies
- Update to latest stable versions
- Clean up development dependencies
- Document all requirements

docker-compose.yml / Dockerfile
- Remove development configurations
- Standardize environment setup
- Clean up unnecessary services
- Optimize for production
```

## Cleanup Checklist

### 1. Search Terms to Eliminate
```bash
# Search for and remove all references to:
- mock
- sample (when used as test data)
- dummy
- placeholder
- test_data
- fake
- generated
- fallback (when used for fake data)
- default_content
- example_data
- demo_data
```

### 2. Code Patterns to Remove
```python
# Remove patterns like:
if not real_data:
    return mock_data

# Remove fallback logic like:
try:
    real_data = get_real_data()
except:
    return fallback_data

# Remove data generation like:
def generate_sample_data():
    return fake_data
```

### 3. Files to Clean or Remove
- Any `.sample` or `.example` files
- Development configuration files
- Test data files in production code
- Cached data from development
- Log files with mixed real/fake data

## Validation Steps

### 1. Code Validation
- [ ] No references to mock/sample/dummy data
- [ ] All functions return real data or proper errors
- [ ] No hardcoded content or fallback data
- [ ] Clear data flow from source to display

### 2. Runtime Validation
- [ ] All API calls return actual data or fail properly
- [ ] No mixing of real and generated content
- [ ] Proper error messages for data issues
- [ ] Clear attribution for all displayed content

### 3. Data Integrity Validation
- [ ] All GSE IDs match their content
- [ ] All titles and summaries are from correct sources
- [ ] All metadata is properly attributed
- [ ] No cross-contamination between datasets

## Tools and Scripts for Cleanup

### 1. Search and Replace Scripts
```bash
# Find all mock data references
grep -r "mock\|sample\|dummy\|placeholder" --include="*.py" --include="*.js" .

# Find hardcoded data
grep -r "GSE[0-9]\+" --include="*.py" --include="*.js" .

# Find fallback logic
grep -r "fallback\|default.*data\|backup.*data" --include="*.py" .
```

### 2. Validation Scripts
```python
def validate_codebase_cleanliness():
    """Ensure no mock data remains in codebase"""
    # Check for forbidden patterns
    # Validate data sources
    # Verify error handling
    pass

def verify_data_integrity():
    """Verify all data is properly sourced"""
    # Check GSE ID consistency
    # Validate content attribution
    # Verify metadata accuracy
    pass
```

### 3. Monitoring Scripts
```python
def monitor_data_quality():
    """Continuous monitoring of data quality"""
    # Real-time validation
    # Data consistency checks
    # Error rate monitoring
    pass
```

## Success Criteria

### 1. Code Cleanliness
- [ ] Zero references to mock/sample/dummy data
- [ ] All functions have clear, single purposes
- [ ] Consistent error handling throughout
- [ ] Clean, documented code structure

### 2. Data Purity
- [ ] All data comes from authoritative sources
- [ ] No mixing of real and generated content
- [ ] Proper attribution for all information
- [ ] Clear data provenance tracking

### 3. System Reliability
- [ ] Predictable behavior under all conditions
- [ ] Proper error handling and recovery
- [ ] Clear debugging and monitoring capabilities
- [ ] Maintainable and extensible architecture

## Timeline

### Day 1-2: Quick Cleanup
- Remove obvious mock data references
- Clean up imports and unused code
- Remove development artifacts

### Day 3-4: Deep Cleanup
- Standardize data processing
- Clean up error handling
- Remove complex fallback logic

### Day 5-6: Validation and Testing
- Validate cleanup completeness
- Test system behavior
- Verify data integrity

### Day 7: Final Preparation
- Document cleaned codebase
- Prepare investigation tools
- Set up monitoring systems

## Next Steps

1. **Execute this cleanup plan systematically**
2. **Validate each cleanup step**
3. **Begin the data integrity investigation**
4. **Implement permanent quality assurance measures**

This cleanup will provide a solid foundation for investigating and fixing the data integrity issues while ensuring they don't recur.
