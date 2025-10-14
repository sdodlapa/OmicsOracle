# Mapping Mechanism Documentation Summary

**Created:** October 13, 2025
**Question:** How does OmicsOracle maintain correct dataset-to-PDF mappings when downloading and analyzing in different orders?

---

## Documents Created

### 1. **Comprehensive Explanation**
📄 **File:** `docs/DATA_FLOW_AND_MAPPING_MECHANISM.md`

**Contents:**
- Complete data flow from frontend to backend to database
- Step-by-step walkthrough with code examples
- Detailed explanation of the unique identifier chain
- Phase-by-phase breakdown (Search → Download → AI Analysis)
- Why mixing cannot occur (3 isolation mechanisms)
- Verification methods and testing procedures

**Use this when:** You need the complete technical understanding with code examples

---

### 2. **Visual Diagrams**
📊 **File:** `docs/architecture/dataset_mapping_flow.md`

**Contents:**
- High-level architecture diagram
- Sequence diagrams for Download and AI Analysis flows
- Object lifecycle visualization
- Key isolation points illustrated
- Manual testing procedures
- ASCII art diagrams showing data flow

**Use this when:** You prefer visual learning or need to present the mechanism

---

### 3. **Quick Reference**
⚡ **File:** `docs/QUICK_MAPPING_EXPLANATION.md`

**Contents:**
- TL;DR answer with restaurant analogy
- 3-step simplified explanation
- Why mixing cannot happen (concise version)
- Order independence proof
- Code verification snippets
- Quick summary of guarantees

**Use this when:** You need a fast answer or want to explain to someone else

---

## Key Concepts

### The Three Unique Identifiers

1. **GEO ID** (e.g., `GSE123456`)
   - Globally unique from NCBI GEO database
   - Never changes throughout pipeline
   - Primary key for dataset identity

2. **Array Index** (e.g., `currentResults[0]`)
   - Stable mapping in frontend
   - Button clicks reference specific index
   - Index-to-dataset binding maintained

3. **PMID** (e.g., `12345`)
   - Globally unique from PubMed (26M+ papers)
   - Used for PDF filenames
   - Links papers to datasets

---

## Three Isolation Mechanisms

### 1. Frontend Object Encapsulation
```javascript
// Each dataset is a separate JavaScript object
currentResults[0] = { geo_id: "GSE123456", fulltext: [A, B] };
currentResults[1] = { geo_id: "GSE789012", fulltext: [C, D] };

// Arrays are NOT shared
currentResults[0].fulltext !== currentResults[1].fulltext  // ✅
```

### 2. Backend Independent Processing
```python
for dataset in datasets:  # One at a time
    dataset.fulltext = []  # NEW array for THIS dataset
    for pub in publications:  # Publications from THIS dataset's PMIDs
        dataset.fulltext.append(parsed)  # Append to THIS dataset only
```

### 3. Database Unique Filenames
```bash
data/fulltext/pdfs/
├── PMID_12345.pdf  # Cannot collide with PMID_11111.pdf
├── PMID_67890.pdf  # PMIDs are globally unique
├── PMID_11111.pdf
└── PMID_22222.pdf
```

---

## Quick Answer

**Q: How does the system prevent mixing PDFs between datasets?**

**A:** Each dataset carries its **unique GEO ID** (like "GSE123456") throughout the entire pipeline. When PDFs are downloaded and parsed, they're attached to that specific dataset's `fulltext` array. When AI analysis is requested, it reads **only that dataset's array** - it's impossible to read another dataset's PDFs because they're stored in different object instances.

**Analogy:** It's like restaurant orders - each table (dataset) has a table number (GEO ID), and food (PDFs) is delivered with that table number. Even if orders are delivered out of sequence, Table 1 always gets Table 1's food because the label (GEO ID) never changes.

---

## Code Locations

### Frontend
- **File:** `omics_oracle_v2/api/static/dashboard_v2.html`
- **Key Functions:**
  - `downloadPapersForDataset(index)` - Line ~1200
  - `selectDataset(index)` - Line ~1502
  - `displayResults(results)` - Line ~1340

### Backend
- **File:** `omics_oracle_v2/api/routes/agents.py`
- **Key Endpoints:**
  - `POST /enrich-fulltext` - Line ~390
  - `POST /analyze` - Line ~730

### Data Models
- **File:** `omics_oracle_v2/api/models/responses.py`
- **Key Models:**
  - `DatasetResponse` - Line ~69 (includes `fulltext` array)
  - `FullTextContent` - Nested in dataset

---

## Verification Test

**To verify the mechanism works:**

1. Open dashboard: `http://localhost:8000/dashboard`
2. Search for datasets with multiple results (3+)
3. Download papers in order: Card 1, Card 0, Card 2
4. Wait 1 minute
5. Analyze in different order: Card 2, Card 0, Card 1
6. Check browser console:
   ```javascript
   console.log(currentResults[0].geo_id);  // Should be different from [1]
   console.log(currentResults[0].fulltext[0].pmid);  // Should be different from [1]
   ```
7. Check AI analysis mentions correct PMID numbers

**Expected:** Each card's AI analysis mentions **only its own PMIDs** ✅

---

## Common Questions

### Q1: What if two users download the same dataset?
**A:** Each user has their own `currentResults` array in their browser session. Backend processes are independent. PDFs are cached in shared storage (by PMID), so second user gets faster downloads, but each user's dataset object maintains its own `fulltext` array with correct references.

### Q2: What if I refresh the page after downloading?
**A:** `currentResults` is stored in browser memory (not persistent). Refreshing clears it. You'd need to search again and re-download. However, PDFs remain cached in `data/fulltext/pdfs/`, so re-downloading is faster.

### Q3: Can I download the same dataset twice?
**A:** Yes. Each download replaces `currentResults[index]` with fresh data. The `fulltext` array is rebuilt from PDFs each time. Old data is discarded (garbage collected).

### Q4: What if a PDF file is corrupted?
**A:** Parsing will fail for that specific PMID. That paper won't be added to `dataset.fulltext`, but other papers in the same dataset will still be processed correctly. The dataset's `fulltext_status` will be marked as `"partial"` instead of `"available"`.

---

## Related Features

### Retry Logic
- **Location:** `omics_oracle_v2/lib/enrichment/fulltext/download_manager.py`
- **Mechanism:** 2 attempts per URL with 1.5s delay
- **Prevents:** Transient failures from causing permanent download failures

### URL Fallback
- **Location:** `omics_oracle_v2/lib/enrichment/fulltext/manager.py`
- **Mechanism:** Tries all 11 sources in sequence until one succeeds
- **Ensures:** Maximum PDF availability

### Full-Text Parsing
- **Location:** `omics_oracle_v2/lib/enrichment/fulltext/parser.py`
- **Extracts:** Abstract, Methods, Results, Discussion, Introduction, Conclusion
- **Used by:** AI analysis to provide detailed insights

---

## Summary

**The mapping mechanism is foolproof because:**

1. ✅ **Unique identifiers** (GEO ID + PMID) flow through entire system
2. ✅ **Object encapsulation** prevents array sharing between datasets
3. ✅ **Independent processing** in backend loops (one dataset at a time)
4. ✅ **Unique filenames** in database (PMID-based, no collisions)
5. ✅ **Order independence** - download and analyze in any sequence

**Result:** You can click Download and AI Analysis buttons in **any order** on **any cards**, and the system will **always** use the correct PDFs for each dataset! 🎯

---

## Further Reading

- Full technical explanation: `docs/DATA_FLOW_AND_MAPPING_MECHANISM.md`
- Visual diagrams: `docs/architecture/dataset_mapping_flow.md`
- Quick reference: `docs/QUICK_MAPPING_EXPLANATION.md`
- Implementation details: See code files listed above
