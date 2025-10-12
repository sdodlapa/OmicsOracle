# Integration Plan - Executive Summary
**Date:** October 12, 2025  
**Audience:** Quick reference for implementation team

## My Understanding (Plain English)

### The Problem
You search for GEO datasets and get results, but you can't easily access the **scientific papers** (PDFs and fulltext) that describe those datasets. The papers exist in PubMed, but they're not connected to the GEO search results.

### The Solution
Create a **lazy loading pipeline** that:
1. Shows GEO results immediately (fast)
2. Fetches paper metadata when user clicks "Get Citations" (medium)
3. Downloads PDFs when user clicks "Download PDFs" (slow)
4. Displays fulltext when user clicks "View Fulltext" (fast from cache)

### The Connection
```
GEO Dataset → PMIDs → Citations → PDFs → Fulltext
                ↑                           ↑
         (linking key)              (normalized content)
```

**Key insight:** The **PMID list** in GEO metadata is the linking key that connects everything.

---

## Visual Flow (Simple)

### CURRENT STATE (Disconnected)
```
┌─────────────────┐
│ Search "diabetes"│
└────────┬────────┘
         │
         ▼
┌────────────────────────────┐
│ GEO Results                │
│                            │
│ GSE123456                  │
│ Title: "Diabetes study..." │
│ Organism: Homo sapiens     │
│ Samples: 24                │
│ Publications: 2 linked     │  ← User sees this but can't access papers
│                            │
│ [No way to view papers]    │  ✗ BROKEN LINK
└────────────────────────────┘
```

### DESIRED STATE (Connected)
```
┌─────────────────┐
│ Search "diabetes"│
└────────┬────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│ GEO Results                                        │
│                                                    │
│ GSE123456 - "Diabetes study..."                   │
│ Organism: Homo sapiens  │  Samples: 24            │
│ Publications: 2 linked (PMID: 12345678, 87654321) │ ← PMIDs are the key!
│                                                    │
│ ┌──────────────┐                                  │
│ │Get Citations │ ← CLICK                          │
│ └──────┬───────┘                                  │
└────────┼──────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│ Citations Found                                    │
│                                                    │
│ 1. PMID:12345678                                   │
│    "Diabetes and RNA-seq analysis..."             │
│    Authors: Smith et al.                           │
│    Journal: Nature, 2023                           │
│                                                    │
│ 2. PMID:87654321                                   │
│    "Pancreatic islet transcriptomics..."           │
│    Authors: Jones et al.                           │
│    Journal: Cell, 2023                             │
│                                                    │
│ ┌──────────────┐                                  │
│ │Download PDFs │ ← CLICK                          │
│ └──────┬───────┘                                  │
└────────┼──────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│ PDFs Downloaded & Parsed                           │
│                                                    │
│ ✓ PMID:12345678 - Downloaded & parsed              │
│ ✓ PMID:87654321 - Downloaded & parsed              │
│                                                    │
│ Saved to: data/pdfs/GSE123456/                     │
│ Parsed to: data/fulltext/parsed/                   │
│                                                    │
│ ┌──────────────┐                                  │
│ │View Fulltext │ ← CLICK                          │
│ └──────┬───────┘                                  │
└────────┼──────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│ Fulltext Display                                   │
│                                                    │
│ 📄 PMID:12345678 - "Diabetes and RNA-seq..."       │
│                                                    │
│ Abstract                                           │
│ This study investigates diabetes...               │
│                                                    │
│ ▼ Introduction                                     │
│ ▼ Methods                                          │
│ ▼ Results                                          │
│   - Gene expression analysis revealed...           │
│   - Table 1: Differentially expressed genes        │
│   - Figure 1: Volcano plot                         │
│ ▼ Discussion                                       │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## Data Flow (Step by Step)

### Step 1: GEO Search (FAST - 2 seconds)
```
User query: "diabetes RNA-seq"
     ↓
UnifiedSearchPipeline.search()
     ↓
GEO E-utilities API
     ↓
Returns:
{
  "geo_id": "GSE123456",
  "title": "Diabetes RNA-seq study",
  "summary": "...",
  "organism": "Homo sapiens",
  "sample_count": 24,
  "pubmed_ids": ["12345678", "87654321"]  ← KEY FIELD!
}
     ↓
Display in dashboard (NO PDFs downloaded yet)
```

### Step 2: Citation Discovery (MEDIUM - 1-2 seconds)
```
User clicks: "Get Citations"
     ↓
For each PMID in pubmed_ids:
  PubMed API → fetch citation metadata
     ↓
Returns:
[
  {
    "pmid": "12345678",
    "title": "Diabetes and RNA-seq analysis",
    "authors": "Smith J, Jones K",
    "journal": "Nature",
    "year": "2023",
    "doi": "10.1038/nature12345"
  },
  ...
]
     ↓
Cache to: data/geo_citation_collections/GSE123456/citations.json
Display in dashboard (NO PDFs downloaded yet)
```

### Step 3: PDF Download (SLOW - 10-30 seconds)
```
User clicks: "Download PDFs"
     ↓
GEOCitationPipeline.discover_and_download(geo_id, pmids)
     ↓
For each PMID:
  1. Try Unpaywall API → PDF URL?
     ├─ Yes → Download PDF bytes
     └─ No → Try PMC API → PDF URL?
         ├─ Yes → Download PDF bytes
         └─ No → Mark as "not available"
  
  2. Save PDF:
     data/pdfs/GSE123456/PMID_12345678.pdf
  
  3. Parse PDF to text:
     PDFParser → raw text
  
  4. Normalize format:
     ContentNormalizer → structured JSON
  
  5. Cache:
     data/fulltext/parsed/PMID_12345678.json
     data/fulltext/parsed/PMID_12345678_normalized.json
     ↓
Returns:
{
  "pdfs_downloaded": 2,
  "pdfs_failed": 0,
  "download_status": {
    "12345678": "success",
    "87654321": "success"
  }
}
     ↓
Display status in dashboard (PDFs ready for viewing)
```

### Step 4: Fulltext Viewing (FAST - <1 second, from cache)
```
User clicks: "View Fulltext"
     ↓
ParsedCache.get_normalized(pmid="12345678")
     ↓
Load from: data/fulltext/parsed/PMID_12345678_normalized.json
     ↓
Returns:
{
  "sections": [
    {"title": "Abstract", "content": "..."},
    {"title": "Introduction", "content": "..."},
    {"title": "Methods", "content": "..."},
    {"title": "Results", "content": "..."},
    {"title": "Discussion", "content": "..."}
  ],
  "tables": [
    {"caption": "Table 1", "data": [[...]]}
  ],
  "figures": [
    {"caption": "Figure 1", "image_url": "..."}
  ]
}
     ↓
Display in expandable sections (like an accordion)
```

---

## File Storage Strategy

### Organization
```
data/
├── pdfs/
│   ├── GSE123456/                    ← Organized by GEO ID
│   │   ├── PMID_12345678.pdf
│   │   ├── PMID_87654321.pdf
│   │   └── metadata.json             ← Collection metadata
│   │
│   └── GSE789012/
│       └── PMID_99999999.pdf
│
├── fulltext/
│   └── parsed/
│       ├── PMID_12345678.json        ← Original parsed (JATS/PDF format)
│       ├── PMID_12345678_normalized.json  ← Normalized format
│       ├── PMID_87654321.json
│       └── PMID_87654321_normalized.json
│
└── geo_citation_collections/
    └── GSE123456/
        ├── citations.json            ← Cached citation metadata
        ├── download_status.json      ← Download progress
        └── metadata.json             ← Collection info
```

### Why this structure?

**By GEO ID (data/pdfs/GSE*/):**
- Easy to find all PDFs for a specific dataset
- User can download entire collection
- Clean separation between datasets

**By PMID (data/fulltext/parsed/PMID_*):**
- Same paper can link to multiple GEO datasets
- Avoid duplicate parsing
- Reuse cached content across datasets

**Mapping file (citations.json):**
```json
{
  "geo_id": "GSE123456",
  "citations": [
    {
      "pmid": "12345678",
      "pdf_path": "data/pdfs/GSE123456/PMID_12345678.pdf",
      "fulltext_path": "data/fulltext/parsed/PMID_12345678_normalized.json",
      "download_status": "success"
    },
    {
      "pmid": "87654321",
      "pdf_path": "data/pdfs/GSE123456/PMID_87654321.pdf",
      "fulltext_path": "data/fulltext/parsed/PMID_87654321_normalized.json",
      "download_status": "success"
    }
  ]
}
```

---

## Implementation Checklist

### Phase 1: Update Dashboard Search ✅ (Ready to implement)
- [ ] Replace `PublicationSearchPipeline` with `SearchAgent`
- [ ] Add "GEO" option to database selector
- [ ] Test: GEO search returns results

**Files to modify:**
- `omics_oracle_v2/lib/dashboard/app.py` (line 281-293)

**Estimated time:** 2-3 hours

### Phase 2: Display GEO Results ✅ (Ready to implement)
- [ ] Create `GEODatasetCard` component
- [ ] Show metadata: geo_id, title, organism, samples
- [ ] Show PMID count: "📚 2 publications linked"
- [ ] Test: GEO cards display correctly

**Files to modify:**
- `omics_oracle_v2/lib/dashboard/components.py`

**Estimated time:** 2 hours

### Phase 3: Citation Discovery ✅ (Ready to implement)
- [ ] Add "Get Citations" button to GEO cards
- [ ] Fetch citation metadata from PubMed
- [ ] Cache to `data/geo_citation_collections/`
- [ ] Display citation list with titles, authors, DOIs
- [ ] Test: Citations load and display

**Files to modify:**
- `omics_oracle_v2/lib/dashboard/app.py`
- `omics_oracle_v2/lib/dashboard/components.py`

**Estimated time:** 2 hours

### Phase 4: PDF Download ✅ (Pipeline already exists!)
- [ ] Add "Download PDFs" button (appears after citations loaded)
- [ ] Call `GEOCitationPipeline.discover_and_download()`
- [ ] Show progress: "Downloading 1/2..."
- [ ] Show results: "✓ 2/2 PDFs downloaded"
- [ ] Test: PDFs download to `data/pdfs/GSE*/`

**Files to modify:**
- `omics_oracle_v2/lib/dashboard/app.py`

**Files to use (already exist):**
- `omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py` ✓
- `omics_oracle_v2/lib/fulltext/pdf_parser.py` ✓
- `omics_oracle_v2/lib/fulltext/normalizer.py` ✓

**Estimated time:** 3 hours

### Phase 5: Fulltext Viewing ✅ (Cache already exists!)
- [ ] Add "View Fulltext" button (appears after PDFs downloaded)
- [ ] Load normalized content from `ParsedCache`
- [ ] Display sections in expandable format
- [ ] Display tables as dataframes
- [ ] Display figure captions
- [ ] Test: Fulltext displays correctly

**Files to modify:**
- `omics_oracle_v2/lib/dashboard/components.py`

**Files to use (already exist):**
- `omics_oracle_v2/lib/fulltext/cache.py` ✓

**Estimated time:** 2 hours

---

## What I Need to Do (Implementation)

### Option A: I implement everything (Recommended)
**Time:** ~11-13 hours total
**Benefit:** Complete working solution

### Option B: We implement together
**Time:** Variable
**Benefit:** You learn the codebase, can customize

### Option C: You implement, I guide
**Time:** Variable
**Benefit:** You control the pace

**My recommendation:** Option A - I implement the dashboard integration following the plan in `COMPLETE_INTEGRATION_FLOW.md`, then you can test and customize.

---

## Success Criteria

### After implementation, users should be able to:
1. ✅ Search for GEO datasets (e.g., "diabetes RNA-seq")
2. ✅ See GEO results with metadata (organism, samples, etc.)
3. ✅ Click "Get Citations" → See list of linked papers
4. ✅ Click "Download PDFs" → Download papers to disk
5. ✅ Click "View Fulltext" → Read parsed content in dashboard
6. ✅ Navigate between sections (Abstract, Methods, Results, etc.)
7. ✅ View tables and figures inline

### Performance expectations:
- Search: <5 seconds (already working via API)
- Citation discovery: <2 seconds (PubMed API)
- PDF download: 10-30 seconds (depends on paper count and sources)
- Fulltext viewing: <1 second (from cache)
- Second search (cached): <100ms (Redis cache hit)

---

## Questions Resolved

### Q: Do we download PDFs for ALL search results automatically?
**A:** NO - Only when user clicks "Download PDFs" for a specific result (lazy loading)

### Q: Where do we store files?
**A:** 
- PDFs: `data/pdfs/{geo_id}/PMID_*.pdf` (by GEO ID)
- Fulltext: `data/fulltext/parsed/PMID_*.json` (by PMID)
- Mapping: `data/geo_citation_collections/{geo_id}/citations.json`

### Q: How do we connect GEO datasets to PDFs?
**A:** Through **PMIDs** in GEO metadata → Citation metadata → PDF files → Fulltext

### Q: How do we avoid re-downloading?
**A:** 
- Check cache before fetching citations
- Check disk before downloading PDFs
- Use ParsedCache for normalized content

### Q: What if PDF is not available?
**A:** Mark as "not available" in download status, show warning in UI

### Q: Can one paper link to multiple GEO datasets?
**A:** YES - That's why we store fulltext by PMID (reusable), not by GEO ID

---

## Next Steps

**Ready to proceed?** I can implement the dashboard integration now following this plan. It will:
1. ✅ Use the working UnifiedSearchPipeline (already in API)
2. ✅ Use the working GEOCitationPipeline (already tested)
3. ✅ Use the working ParsedCache (Phase 5 completed)
4. ✅ Connect all pieces with lazy loading pattern

Just say "implement it" and I'll start! 🚀
