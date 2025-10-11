# 📚 OmicsOracle Examples

This directory contains **runnable examples** demonstrating OmicsOracle's features, pipelines, and integrations.

---

## 🚀 Quick Start

**First time?** Run the quick test to validate your setup:

```bash
cd /path/to/OmicsOracle
python quick_test.py
```

This will verify:
- ✅ Environment setup
- ✅ API connectivity
- ✅ Core features working
- ✅ Sprint 1 parallel fetching

---

## 📂 Directory Structure

### 🎯 [Sprint Demos](sprint-demos/)
Feature demonstrations organized by sprint/development phase:
- **Sprint 1 Parallel Fetching** - 10x performance improvement demo
- **OpenAlex Integration** - Publication search integration
- **OpenAlex Search** - Advanced search capabilities

### 🔧 [Pipeline Examples](pipeline-examples/)
Real-world pipeline usage examples:
- **GEO Citation Pipeline** - Complete GEO → Citations → PDFs workflow
- **Optimized Pipeline** - Performance-optimized citation collection
- **Query Preprocessing** - Advanced query optimization
- **Comprehensive Pipeline** - Full-featured pipeline demo

### ✨ [Feature Examples](feature-examples/)
Individual feature demonstrations:
- **Synonym Expansion** - Biomedical synonym handling
- **Genomic Terms** - Domain-specific term processing
- **GEO Synonym Integration** - GEO-specific synonyms
- **Full Features** - All features enabled demo

### 🔍 [Validation Scripts](validation/)
One-off validation and testing scripts:
- **DNA Methylation HiC** - Specific use case validation
- **Citation Fixes** - Citation bug fix validation
- **Email Config** - Email configuration testing
- **OpenAlex GEO** - OpenAlex + GEO integration validation

---

## 💡 Usage Patterns

### Running Examples

All examples are standalone Python scripts:

```bash
# Activate virtual environment
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Run any example
python examples/sprint-demos/sprint1-parallel-fetching.py
python examples/pipeline-examples/geo-citation-pipeline.py
python examples/feature-examples/synonym-expansion.py
```

### Common Setup

Most examples require:

1. **Environment Variables** (`.env` file):
   ```bash
   NCBI_EMAIL=your.email@example.com
   NCBI_API_KEY=your_ncbi_api_key
   OPENAI_API_KEY=your_openai_key  # For AI features
   ```

2. **SSL Configuration** (for institutional networks):
   ```bash
   SSL_VERIFY=false  # If behind Georgia Tech VPN or similar
   ```

3. **Virtual Environment**:
   ```bash
   source venv/bin/activate
   ```

---

## 📖 Related Documentation

- **[Pipeline Decision Guide](../docs/pipelines/PIPELINE_DECISION_GUIDE.md)** - Choose the right pipeline
- **[API Reference](../docs/API_REFERENCE.md)** - Complete API documentation
- **[Quick Start Guide](../docs/STARTUP_GUIDE.md)** - Get up and running
- **[Developer Guide](../docs/DEVELOPER_GUIDE.md)** - Development setup

---

## 🎓 Learning Path

**New to OmicsOracle?** Follow this learning path:

1. **Start Here**: Run `quick_test.py` in root directory
2. **Sprint Demos**: See what's new in each sprint
3. **Pipeline Examples**: Learn pipeline usage patterns
4. **Feature Examples**: Explore individual features
5. **Validation Scripts**: Advanced use cases

---

## 🤝 Contributing Examples

Have a useful example? Please contribute!

1. Place it in the appropriate directory
2. Add clear docstrings explaining:
   - What the example demonstrates
   - Prerequisites needed
   - Expected output
3. Update the relevant README
4. Submit a pull request

---

## 📧 Support

Questions about examples?
- Check the relevant README in each subdirectory
- Review [documentation](../docs/)
- Create an issue on GitHub

---

**Happy Learning!** 🎉
