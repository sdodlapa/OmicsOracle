# 🎯 Dataset-to-PDF Mapping - Visual Cheat Sheet

**Question:** How does OmicsOracle prevent mixing PDFs between datasets?

---

## 📊 The Architecture (One Glance)

```
┌──────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Browser)                            │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ currentResults = [                                              │  │
│  │   [0] { geo_id: "GSE123456", fulltext: [PDF_A, PDF_B] } ◄───┐  │  │
│  │   [1] { geo_id: "GSE789012", fulltext: [PDF_C, PDF_D] } ◄───┼──│  │
│  │   [2] { geo_id: "GSE555555", fulltext: [PDF_E, PDF_F] } ◄───┼──│  │
│  │ ]                                                             │  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Card 0 [Download] [AI] ─┐                                          │
│  Card 1 [Download] [AI] ─┼── Each button knows its index           │
│  Card 2 [Download] [AI] ─┘                                          │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
                   │ Send dataset with geo_id + PMIDs
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                              │
│                                                                       │
│  for dataset in datasets:  ◄── Process ONE at a time                 │
│      dataset.fulltext = [] ◄── NEW array each time                   │
│                                                                       │
│      Download PDFs for THIS dataset's PMIDs only                     │
│      Parse PDFs                                                       │
│      dataset.fulltext.append(parsed) ◄── Attach to THIS dataset      │
│                                                                       │
│  Return: dataset with populated fulltext array                       │
└──────────────────┬────────────────────────────────────────────────────┘
                   │
                   │ Save/Read PDFs
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     DATABASE (File System)                            │
│                                                                       │
│  data/fulltext/pdfs/                                                  │
│    ├─ PMID_12345.pdf ◄── From GSE123456                              │
│    ├─ PMID_67890.pdf ◄── From GSE123456                              │
│    ├─ PMID_11111.pdf ◄── From GSE789012                              │
│    ├─ PMID_22222.pdf ◄── From GSE789012                              │
│    └─ ...                                                             │
│                                                                       │
│  ✅ Each file has unique PMID-based name (no collisions)             │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔒 Three Locks That Prevent Mixing

### Lock 1: Object Encapsulation
```
┌─────────────────────────┐     ┌─────────────────────────┐
│   Dataset Object 0      │     │   Dataset Object 1      │
│                         │     │                         │
│  geo_id: "GSE123456"    │  ≠  │  geo_id: "GSE789012"    │
│  fulltext: [A, B]  ◄────┼─────┼──► fulltext: [C, D]     │
│                         │     │                         │
│  ✅ Separate in memory  │     │  ✅ No shared reference  │
└─────────────────────────┘     └─────────────────────────┘
```

### Lock 2: Independent Processing
```
Backend Loop:

Iteration 1:
  dataset = GSE123456
  dataset.fulltext = []  ← NEW array
  Add papers A & B to THIS array

Iteration 2:
  dataset = GSE789012
  dataset.fulltext = []  ← NEW array (unrelated to iteration 1)
  Add papers C & D to THIS array

✅ Each iteration works on different array instance
```

### Lock 3: Unique Filenames
```
PMID_12345.pdf ─────► Belongs to GSE123456
PMID_67890.pdf ─────► Belongs to GSE123456
PMID_11111.pdf ─────► Belongs to GSE789012
PMID_22222.pdf ─────► Belongs to GSE789012

✅ PMIDs are globally unique (26M+ in PubMed)
✅ No filename collisions possible
```

---

## 🎯 The Identifier Chain

```
GEO ID                PMID                PDF File            Parsed Text
─────────────────────────────────────────────────────────────────────────

GSE123456 ──────────► 12345 ──────────► PMID_12345.pdf ──────► {methods:"..."}
    │                   │                      │                     │
    │                   │                      │                     │
    └───────────────────┴──────────────────────┴─────────────────────┘
                                      │
                            Attached to dataset.fulltext[0]
                                      │
                            Used in AI analysis for GSE123456 ONLY

────────────────────────────────────────────────────────────────────────

GSE789012 ──────────► 11111 ──────────► PMID_11111.pdf ──────► {methods:"..."}
    │                   │                      │                     │
    │                   │                      │                     │
    └───────────────────┴──────────────────────┴─────────────────────┘
                                      │
                            Attached to dataset.fulltext[0]
                                      │
                            Used in AI analysis for GSE789012 ONLY

✅ Separate chains - cannot cross!
```

---

## 🔄 Order Independence Proof

### Download Order: 1 → 0 → 2
```
Time 1: currentResults[1] = enrich(GSE789012)  ← Updates index 1
Time 2: currentResults[0] = enrich(GSE123456)  ← Updates index 0
Time 3: currentResults[2] = enrich(GSE555555)  ← Updates index 2

Result:
  [0] = GSE123456 with PDFs A, B ✅
  [1] = GSE789012 with PDFs C, D ✅
  [2] = GSE555555 with PDFs E, F ✅
```

### AI Analysis Order: 2 → 0 → 1
```
Time 1: analyze(currentResults[2])  ← Uses GSE555555's PDFs (E, F) ✅
Time 2: analyze(currentResults[0])  ← Uses GSE123456's PDFs (A, B) ✅
Time 3: analyze(currentResults[1])  ← Uses GSE789012's PDFs (C, D) ✅

✅ Each analysis uses correct dataset's PDFs
✅ Order doesn't matter!
```

---

## 🧪 Quick Test

### In Browser Console
```javascript
// After downloading papers for multiple datasets:

console.log(currentResults[0].geo_id);
// Output: "GSE123456"

console.log(currentResults[1].geo_id);
// Output: "GSE789012" ← Different!

console.log(currentResults[0].fulltext === currentResults[1].fulltext);
// Output: false ← Separate arrays! ✅
```

---

## 📚 Documentation Map

```
START HERE → README_MAPPING_MECHANISM.md (this file)
             │
             ├─ 2 min  → ANSWER_SUMMARY_MAPPING_MECHANISM.md
             ├─ 5 min  → QUICK_MAPPING_EXPLANATION.md
             ├─ 15 min → architecture/dataset_mapping_flow.md
             └─ 20 min → DATA_FLOW_AND_MAPPING_MECHANISM.md
```

---

## ✅ The Answer (TL;DR)

**Q:** How to prevent PDF mixing between datasets?

**A:** Three mechanisms working together:

1. **Unique IDs** (GEO ID + PMID) that never change
2. **Separate arrays** (each dataset has its own `fulltext` array)
3. **Independent loops** (backend processes one dataset at a time)

**Result:** Architecturally impossible to mix! 🎯

---

## 💡 Mental Model

Think of it like **labeled boxes**:

```
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│   Box #123456    │   │   Box #789012    │   │   Box #555555    │
│   ─────────────  │   │   ─────────────  │   │   ─────────────  │
│   Paper A        │   │   Paper C        │   │   Paper E        │
│   Paper B        │   │   Paper D        │   │   Paper F        │
└──────────────────┘   └──────────────────┘   └──────────────────┘

When you ask for "Box #123456", you get papers A & B.
You CANNOT get papers from Box #789012 by mistake!

Why? Because the box number (GEO ID) is unique and clearly labeled.
```

---

## 🎓 Code Snippets

### Frontend (JavaScript)
```javascript
// Download button
async function downloadPapersForDataset(index) {
    const dataset = currentResults[index];  // Get by index
    const enriched = await download(dataset);
    currentResults[index] = enriched;  // Replace same index
}

// AI button
async function selectDataset(index) {
    const dataset = currentResults[index];  // Get by index
    await analyze(dataset);  // Analyze with dataset's own fulltext
}
```

### Backend (Python)
```python
# Download endpoint
for dataset in datasets:  # Process one at a time
    dataset.fulltext = []  # NEW array for THIS dataset
    for pub in publications:  # From THIS dataset's PMIDs
        parsed = parse_pdf(pub.pdf_path)
        dataset.fulltext.append(parsed)  # Attach to THIS dataset

# AI endpoint
for ds in request.datasets:  # Loop input datasets
    for ft in ds.fulltext:  # Loop THIS dataset's fulltext
        prompt += ft.methods + ft.results  # Use THIS dataset's papers
```

---

## 🚀 Next Steps

1. ✅ Understand the mechanism (read this cheat sheet)
2. ✅ Test in browser console (verify object separation)
3. ✅ Read detailed docs (choose based on time available)
4. ✅ Review code (see actual implementation)

**You now understand how OmicsOracle maintains perfect dataset-to-PDF mappings!** 🎯

---

**Created:** October 13, 2025
**System:** OmicsOracle v2.0
