# 🎯 Workflow Selection Guide

## Which Workflow Should I Use?

### 🔬 Full Analysis (Recommended for Most Users)

**When to use:**
- You have a general research question
- You want comprehensive, validated results
- Quality matters more than speed
- You need detailed reports

**Example queries:**
- "breast cancer RNA-seq datasets"
- "COVID-19 immune response single-cell"
- "DNA methylation and HiC joint profiling"
- "Alzheimer's disease transcriptomics"

**What happens:**
1. ✅ Query Agent: Analyzes your question using NLP
2. ✅ Search Agent: Finds relevant datasets from NCBI GEO
3. ✅ Data Agent: Validates dataset quality and completeness
4. ✅ Report Agent: Generates comprehensive summary

**Duration**: ~10-30 seconds  
**Results**: High-quality, validated datasets with detailed analysis

---

### ⚡ Simple Search (Fast & Lightweight)

**When to use:**
- You want quick results
- You're just exploring
- You don't need quality validation
- Speed is priority

**Example queries:**
- "cancer genomics"
- "RNA-seq human"
- "ChIP-seq histone modifications"

**What happens:**
1. ✅ Query Agent: Analyzes your question
2. ✅ Search Agent: Finds relevant datasets
3. ✅ Report Agent: Generates summary report
4. ❌ Data Agent: SKIPPED (no validation)

**Duration**: ~5-15 seconds  
**Results**: More results, but not quality-checked

---

### 📄 Quick Report (For Known Dataset IDs)

**When to use:**
- You already have specific GEO dataset IDs
- You want a report about known datasets
- You found datasets elsewhere and want analysis

**Example queries:**
- "GSE12345"
- "GSE12345 GSE67890 GSE99999"
- "Generate report for GDS1234"

**What happens:**
1. ❌ Query Agent: SKIPPED
2. ✅ Search Agent: Retrieves specific datasets by ID
3. ✅ Report Agent: Generates report

**Duration**: ~3-8 seconds  
**Results**: Report about the specific datasets you requested

---

### ✓ Validate Datasets (Quality Check)

**When to use:**
- You have specific GEO IDs to validate
- You want to check dataset quality
- You need completeness assessment
- You're comparing dataset options

**Example queries:**
- "GSE12345 GSE67890" (just the IDs)
- "Validate quality of GSE12345"
- "Check completeness GSE11111 GSE22222"

**What happens:**
1. ✅ Query Agent: Extracts dataset IDs (if mixed with text)
2. ✅ Data Agent: Validates metadata, samples, quality
3. ✅ Report Agent: Generates quality report

**Duration**: ~5-12 seconds  
**Results**: Detailed quality metrics and validation results

---

## 🎬 Usage Examples

### Example 1: General Research

**Scenario**: "I want to study breast cancer genetics"

**Best Workflow**: 🔬 Full Analysis

**Query**: `breast cancer RNA-seq BRCA1 BRCA2`

**Why**: You don't have specific datasets yet, and you want high-quality results with validation.

---

### Example 2: Quick Exploration

**Scenario**: "I want to see what's available for COVID research"

**Best Workflow**: ⚡ Simple Search

**Query**: `COVID-19 immune response`

**Why**: You're exploring, speed matters, and you'll validate later.

---

### Example 3: Known Datasets

**Scenario**: "I found GSE12345 in a paper and want details"

**Best Workflow**: 📄 Quick Report

**Query**: `GSE12345`

**Why**: You have the specific ID and just want information about it.

---

### Example 4: Quality Check

**Scenario**: "I have 3 datasets, which is best quality?"

**Best Workflow**: ✓ Validate Datasets

**Query**: `GSE12345 GSE67890 GSE99999`

**Why**: You want to compare quality metrics to choose the best one.

---

## 📊 Workflow Comparison

| Feature | Full Analysis | Simple Search | Quick Report | Validate Datasets |
|---------|---------------|---------------|--------------|-------------------|
| **Speed** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Needs IDs?** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Validation** | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| **NLP Processing** | ✅ Yes | ✅ Yes | ❌ No | ⚠️ Optional |
| **Best For** | Research | Exploration | Known IDs | Quality Check |

---

## 🚨 Common Mistakes

### ❌ Wrong: Using Data Validation without IDs
```
Workflow: Validate Datasets
Query: "cancer genomics"
Result: ❌ Error - no dataset IDs to validate
```

**Fix**: Use Full Analysis or Simple Search instead

---

### ❌ Wrong: Using Quick Report with general query
```
Workflow: Quick Report
Query: "breast cancer RNA-seq"
Result: ⚠️ No results - needs specific GEO IDs
```

**Fix**: Include dataset IDs like "GSE12345" or use Full Analysis

---

### ❌ Wrong: Using Simple Search when quality matters
```
Workflow: Simple Search
Query: "high-quality breast cancer datasets"
Result: ⚠️ Results not validated - may include low-quality data
```

**Fix**: Use Full Analysis for quality validation

---

## 💡 Pro Tips

### Tip 1: Start with Full Analysis
When in doubt, use **Full Analysis**. It's the most comprehensive and works for any query type.

### Tip 2: Use Simple Search for Broad Exploration
If you're just browsing or need ideas, **Simple Search** is perfect.

### Tip 3: Combine Workflows
1. First: Simple Search to find datasets
2. Then: Validate Datasets to check quality
3. Finally: Quick Report for detailed analysis

### Tip 4: Provide GEO IDs When You Have Them
If you know the dataset IDs:
- Use **Quick Report** for fast info
- Use **Validate Datasets** for quality check

### Tip 5: Better Queries = Better Results
**Good query**:
```
breast cancer RNA-seq tumor vs normal TCGA
```

**Better query**:
```
breast cancer RNA-seq BRCA1 BRCA2 mutations tumor normal comparison
```

---

## 🎯 Decision Tree

```
Start Here
    │
    ├─ Do you have specific GEO dataset IDs?
    │   │
    │   ├─ YES → Want quality check?
    │   │   ├─ YES → ✓ Validate Datasets
    │   │   └─ NO  → 📄 Quick Report
    │   │
    │   └─ NO → How important is quality?
    │       ├─ Very important → 🔬 Full Analysis
    │       └─ Speed matters   → ⚡ Simple Search
```

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Debug Dashboard**: http://localhost:8000/debug/dashboard
- **Example Queries**: See `test_dev_mode.py`

---

## 🆘 Troubleshooting

### "Data validation workflow not yet implemented"
**Problem**: You're using an old version  
**Solution**: Server has been updated! Restart server:
```bash
./start_dev_server.sh
```

### "No datasets found"
**Problem**: Query too specific or NCBI has no matches  
**Solution**: 
- Try broader terms
- Check spelling
- Remove very specific filters

### "Workflow failed"
**Problem**: Something went wrong in processing  
**Solution**:
- Check `/debug/dashboard` for error details
- See trace timeline for exact failure point
- Report trace_id for support

---

**Updated**: October 5, 2025  
**Status**: All workflows now fully implemented! 🎉
