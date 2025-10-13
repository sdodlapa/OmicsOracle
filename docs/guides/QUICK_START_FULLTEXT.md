# Quick Start: Full-Text AI Analysis

**5-Minute Guide to Using the New Feature**

---

## 🚀 Try It Now

### 1. Open Dashboard
```
http://localhost:8000/dashboard
```

### 2. Login (if needed)
- Username: (your credentials)
- Password: (your credentials)

### 3. Search for Datasets
```
Example: "breast cancer RNA-seq"
```

### 4. Watch for PDF Status
After search, you'll see cards with badges:

- **📥 PDF download pending...** (initial)
- **⏳ Downloading PDFs...** (in progress)
- **✓ 2 PDFs available for AI analysis** (ready!)

⏱️ Usually takes 10-30 seconds

### 5. Click AI Analysis
Click the **🤖 AI Analysis** button on any dataset card

### 6. See the Difference!

**Before (GEO Summary Only):**
> "This dataset studies breast cancer using RNA-seq methodology with 8 samples from Homo sapiens."

**After (With Full-Text):**
> "This study employed Illumina HiSeq 4000 sequencing with 150bp paired-end reads, achieving an average depth of 50M reads per sample. The analysis identified 523 differentially expressed genes (FDR < 0.05), with significant enrichment in the BRCA1 DNA repair pathway (p = 0.001).
>
> **Key Experimental Details:**
> - Sample prep: RIN values >8.0 (high quality)
> - Library: TruSeq stranded mRNA kit
> - Replicates: n=4 biological replicates
> - Analysis: DESeq2 with standard normalization
>
> **Recommendation:** Excellent choice for validation studies due to rigorous QC, appropriate statistical power, and detailed methodology that enables reproducibility."

---

## 🔍 What's Happening Behind the Scenes?

```
You search
    ↓
Results appear instantly (1-2s)
    ↓
Background process starts
    ↓
Downloads PDFs from PubMed Central
    ↓
Parses to Methods/Results/Discussion
    ↓
Caches for future use
    ↓
Updates badge: "✓ PDFs available"
    ↓
You click AI Analysis
    ↓
GPT-4 receives full scientific context
    ↓
Returns rich, specific insights
```

---

## 📊 Feature Highlights

### Smart Caching
- PDFs downloaded once, cached forever (7 days)
- Second search for same dataset = instant full-text

### Non-Blocking
- Search stays fast (<3s)
- PDFs download in background
- Use dashboard while waiting

### Graceful Degradation
- No PDFs available? Analysis still works (uses GEO summary)
- Partial PDFs? Uses what's available
- Status always shown: "⚠️ No full-text available"

### Privacy & Security
- PDFs cached locally (not uploaded anywhere)
- Only publicly available PMC papers used
- Respects paywalls (no illegal downloads)

---

## 🎯 Best Use Cases

### 1. Method Comparison
**Query:** "single cell RNA-seq heart"

**AI Analysis Will Tell You:**
- Which datasets used 10X Genomics vs. Smart-seq2
- Cell count and sequencing depth
- Quality metrics (UMI counts, doublet rates)
- Specific reagents and protocols

### 2. Data Quality Assessment
**Query:** "diabetes liver transcriptomics"

**AI Analysis Will Tell You:**
- Sample sizes and statistical power
- Whether replicates were biological or technical
- QC metrics (RIN, mapping rates)
- Whether batch effects were addressed

### 3. Reproducibility Check
**Query:** "CRISPR screen cancer"

**AI Analysis Will Tell You:**
- Exact CRISPR library used
- Cell lines and passage numbers
- Read depth and coverage
- Analysis pipeline details

---

## 🔧 Troubleshooting

### "PDF download pending..." never changes
**Solution:** Some datasets don't have PDFs in PubMed Central
- This is normal - not all papers are open access
- Analysis will still work using GEO summary
- Badge will eventually show "⚠️ No full-text available"

### AI Analysis seems slow
**Check:**
1. Do you see "✓ PDFs available"?
   - Yes → Analysis should be fast (5-10s)
   - No → Wait for PDFs to download first

2. Is OpenAI API key configured?
   ```bash
   echo $OPENAI_API_KEY
   ```

### Analysis still generic
**Verify full-text was downloaded:**
1. Open browser console (F12)
2. Type: `console.log(currentResults[0])`
3. Check: `fulltext_count` should be > 0

---

## 💡 Pro Tips

### 1. Let PDFs Download
After searching, **wait 15-20 seconds** before clicking AI Analysis for best results

### 2. Use Specific Queries
Better: "breast cancer RNA-seq BRCA1"
Not: "cancer"

More specific = better PMIDs = richer full-text

### 3. Compare Multiple Datasets
Click AI Analysis on 2-3 related datasets to compare methodologies

### 4. Check the Status Badge
- Green ✓ = Full-text ready → Rich analysis
- Yellow ⏳ = Still downloading → Wait 10s
- Blue 📥 = Pending → Wait 20s
- No badge = No PMIDs → Will use GEO summary

---

## 📱 Example Workflow

```
9:00 AM - Search "liver fibrosis RNA-seq"
9:00 AM - Get 12 results instantly
9:00 AM - Start reviewing dataset titles while PDFs download
9:01 AM - See "✓ 3 PDFs available" on top 5 datasets
9:01 AM - Click AI Analysis on most relevant dataset
9:01 AM - Get detailed methodology comparison:
          "Dataset A used paired-end 150bp reads with 6
          biological replicates, while Dataset B used
          single-end 50bp with 3 replicates. Dataset A
          has higher statistical power (80% vs 60%) and
          better depth (50M vs 20M reads). Recommend
          Dataset A for validation due to superior QC
          metrics (RIN 8.5±0.3 vs 7.2±0.8)."
9:02 AM - Make informed decision, proceed with Dataset A
```

**Total time:** 2 minutes from search to decision

---

## 🆚 Quick Comparison

| Feature | Without Full-Text | With Full-Text |
|---------|-------------------|----------------|
| **Search Speed** | 2s | 2s ✅ |
| **AI Insights** | Generic | Specific ✅ |
| **Method Details** | None | Complete ✅ |
| **QC Metrics** | None | Included ✅ |
| **Statistical Info** | None | P-values, FDR ✅ |
| **Reproducibility** | Low | High ✅ |
| **Decision Quality** | Basic | Expert-level ✅ |

---

## 📚 Learn More

- **API Docs:** http://localhost:8000/docs
- **Full Guide:** `docs/guides/FULLTEXT_AI_ANALYSIS.md`
- **Technical Details:** `docs/architecture/FULLTEXT_IMPLEMENTATION_COMPLETE.md`

---

## ❓ Questions?

Check the logs:
```bash
tail -f /tmp/omics_api.log
```

Or test the integration:
```bash
python tests/integration/test_fulltext_integration.py
```

---

**🎉 Enjoy richer, more insightful AI analysis!**
