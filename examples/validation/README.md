# Validation Scripts

One-off validation and testing scripts for specific use cases and bug fixes.

---

## 📋 Available Scripts

### DNA Methylation + HiC Flow

**File**: `dna-methylation-hic.py`

**Purpose**: Validate the complete data flow for DNA methylation + Hi-C datasets

**What it validates**:
- Query construction for specific use case
- GEO dataset discovery
- Metadata extraction
- Citation discovery
- Data flow integrity

**Run it**:
```bash
python examples/validation/dna-methylation-hic.py
```

**Expected output**:
- Datasets found: 10-20 relevant GEO datasets
- Citations: 100+ publications
- Validation: Complete data flow verified

---

### Citation Fixes Validation

**File**: `citation-fixes.py`

**Purpose**: Validate bug fixes in citation discovery system

**What it validates**:
- Citation extraction from PubMed
- Citation linking to GEO datasets
- Deduplication logic
- Error handling improvements

**Run it**:
```bash
python examples/validation/citation-fixes.py
```

**Context**: Created during October 2025 citation system improvements

---

### Email Configuration Test

**File**: `email-config.py`

**Purpose**: Test NCBI email configuration and API access

**What it validates**:
- Environment variable setup
- NCBI API key validity
- Email format correctness
- API rate limiting

**Run it**:
```bash
python examples/validation/email-config.py
```

**Expected output**:
- ✅ Email configured correctly
- ✅ API key valid
- ✅ Connection successful

---

### OpenAlex + GEO Integration

**File**: `openalex-geo.py`

**Purpose**: Validate OpenAlex and GEO dataset integration

**What it validates**:
- Cross-referencing between OpenAlex publications and GEO datasets
- Citation network consistency
- Metadata alignment
- Data quality

**Run it**:
```bash
python examples/validation/openalex-geo.py
```

---

## ⚠️ Important Notes

These scripts are **validation tools**, not production code:

- Created for specific testing scenarios
- May have hardcoded test data
- Used during development/debugging
- Kept for regression testing

---

## 🔧 Prerequisites

All validation scripts require:

1. **Environment variables**:
   ```bash
   NCBI_EMAIL=your.email@example.com
   NCBI_API_KEY=your_ncbi_api_key
   ```

2. **Optional**:
   ```bash
   OPENAI_API_KEY=your_openai_key
   SSL_VERIFY=false  # For institutional networks
   ```

---

## 📊 When to Use These

Use validation scripts when:
- Testing specific bug fixes
- Validating new integrations
- Regression testing
- Debugging data flow issues
- Verifying configuration

**Don't use for**:
- Production workflows → Use pipeline examples instead
- Learning → Use feature examples instead
- Performance testing → Use sprint demos instead

---

## 🔍 Related Validation

For more comprehensive validation:
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- E2E tests: `tests/e2e/`

---

## 📖 Historical Context

### DNA Methylation + HiC (Oct 10, 2025)
- Validated query optimization improvements
- Found 18x more datasets than original query
- Verified citation collection pipeline

### Citation Fixes (Oct 9, 2025)
- Fixed deduplication bug
- Improved error handling
- Validated with 100+ citations

### OpenAlex Integration (Oct 2025)
- Added OpenAlex API support
- Cross-referenced with GEO
- Improved publication coverage

---

## 📧 Support

Questions about validation scripts?
- Review session reports in `docs/archive/consolidation-2025-10/`
- Check related documentation
- Create an issue on GitHub
