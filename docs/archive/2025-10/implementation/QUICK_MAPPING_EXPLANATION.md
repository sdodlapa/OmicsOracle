# Quick Answer: Dataset-to-PDF Mapping

**Question:** When downloading multiple datasets and analyzing them in different order, how does the system prevent mixing up parsed PDFs between datasets?

---

## TL;DR Answer

**The system uses three unique identifiers that never change:**

1. **GEO ID** (e.g., `GSE123456`) - Identifies each dataset
2. **Array Index** (e.g., `currentResults[0]`) - Maps UI card to dataset object
3. **PMID** (e.g., `12345`) - Identifies each paper/PDF

**These IDs travel together through the entire pipeline, ensuring correct mapping at every step.**

---

## Simple Analogy

Think of it like a restaurant order system:

```
Table 1: Orders pizza          → Pizza box labeled "Table 1"
Table 2: Orders burger         → Burger bag labeled "Table 2"
Table 3: Orders salad          → Salad bowl labeled "Table 3"

Even if delivered out of order (3, 1, 2):
✅ Table 1 gets pizza (never gets burger by mistake)
✅ Table 2 gets burger (never gets salad by mistake)
✅ Table 3 gets salad (never gets pizza by mistake)

Why? Each order has a TABLE NUMBER that stays with it!
```

In OmicsOracle:
- **Table = Dataset (identified by GEO ID)**
- **Food = PDFs (identified by PMID)**
- **Labels = Unique identifiers that never change**

---

## How It Works (3 Steps)

### Step 1: Each Dataset Has Unique ID

```javascript
currentResults = [
    { geo_id: "GSE123456", fulltext: [] },  // ← Index 0
    { geo_id: "GSE789012", fulltext: [] },  // ← Index 1
    { geo_id: "GSE555555", fulltext: [] }   // ← Index 2
]
```

### Step 2: Download Attaches PDFs to Correct Dataset

When you click "Download Papers" on Card 1 (GSE789012):

```
1. Frontend: Get dataset at index 1 → geo_id = "GSE789012"
2. Backend: Download PDFs for GSE789012's PMIDs → [11111, 22222]
3. Backend: Parse PDFs and attach to SAME dataset object
4. Frontend: Replace currentResults[1] with enriched dataset

Result:
currentResults[1] = {
    geo_id: "GSE789012",  // ← Still same ID
    fulltext: [
        { pmid: "11111", methods: "...", results: "..." },
        { pmid: "22222", methods: "...", results: "..." }
    ]
}
```

**Key Point:** The `fulltext` array is attached to the **SAME dataset object** that has `geo_id = "GSE789012"`. It cannot leak to other datasets.

### Step 3: AI Analysis Uses Dataset's Own PDFs

When you click "AI Analysis" on Card 1:

```
1. Frontend: Get dataset at index 1 → geo_id = "GSE789012" + fulltext array
2. Backend: Loop through THAT dataset's fulltext array
3. Backend: Extract Methods/Results from PMIDs 11111 & 22222 ONLY
4. GPT-4: Receives text from papers 11111 & 22222 (not 12345/67890!)
```

---

## Why Mixing Cannot Happen

### Isolation Mechanism 1: Object Encapsulation

```javascript
// JavaScript creates SEPARATE objects
const dataset1 = { geo_id: "GSE123456", fulltext: [A, B] };
const dataset2 = { geo_id: "GSE789012", fulltext: [C, D] };

// These are INDEPENDENT objects in memory
dataset1.fulltext !== dataset2.fulltext  // ✅ Different arrays

// Impossible to accidentally share:
dataset1.fulltext.push(...dataset2.fulltext);  // ❌ No code does this
```

### Isolation Mechanism 2: Backend Loops Independently

```python
for dataset in datasets:  # Process ONE dataset at a time
    dataset.fulltext = []  # ← NEW array for THIS dataset

    # Get PMIDs from THIS dataset
    pmids = dataset.pubmed_ids  # e.g., ["11111", "22222"]

    # Download PDFs ONLY for THESE PMIDs
    for pmid in pmids:
        pdf = download_pdf(pmid)  # PMID_11111.pdf, PMID_22222.pdf
        parsed = parse_pdf(pdf)

        # Append to THIS dataset's fulltext array
        dataset.fulltext.append(parsed)  # ← Only affects THIS dataset
```

### Isolation Mechanism 3: File System Uses Unique Names

```bash
# Each PDF has unique filename (PMID is globally unique)
data/fulltext/pdfs/
├── PMID_12345.pdf  # From GSE123456
├── PMID_67890.pdf  # From GSE123456
├── PMID_11111.pdf  # From GSE789012
└── PMID_22222.pdf  # From GSE789012

# No filename collisions possible
# Each dataset references its own PDFs via PMID
```

---

## Order Independence

### Download Order: Card 1 → Card 0 → Card 2

```
currentResults[1] = enrich(GSE789012)  // Updates index 1
currentResults[0] = enrich(GSE123456)  // Updates index 0
currentResults[2] = enrich(GSE555555)  // Updates index 2

✅ Each index gets its own enriched dataset
✅ No cross-contamination
```

### AI Analysis Order: Card 2 → Card 0 → Card 1

```
analyze(currentResults[2])  // Uses GSE555555's fulltext
analyze(currentResults[0])  // Uses GSE123456's fulltext
analyze(currentResults[1])  // Uses GSE789012's fulltext ✅ Correct!

✅ Each analysis uses correct dataset's PDFs
✅ Order doesn't matter
```

---

## Visual Summary

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND ARRAY                             │
│                                                               │
│  Index 0 ───► { geo_id: "GSE123456", fulltext: [A, B] }      │
│                                                               │
│  Index 1 ───► { geo_id: "GSE789012", fulltext: [C, D] }      │
│                                                               │
│  Index 2 ───► { geo_id: "GSE555555", fulltext: [E, F] }      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
    Click on             Click on             Click on
    Card 0               Card 1               Card 2
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│                   BACKEND PROCESSING                          │
│                                                               │
│  Process GSE123456    Process GSE789012    Process GSE555555 │
│  ├─ Download A,B      ├─ Download C,D      ├─ Download E,F   │
│  └─ Attach to         └─ Attach to         └─ Attach to      │
│     THIS dataset         THIS dataset         THIS dataset    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│                      DATABASE                                 │
│                                                               │
│  GSE123456 ───► PMID_A.pdf, PMID_B.pdf                       │
│  GSE789012 ───► PMID_C.pdf, PMID_D.pdf                       │
│  GSE555555 ───► PMID_E.pdf, PMID_F.pdf                       │
│                                                               │
│  ✅ Each dataset's PDFs stored separately                    │
│  ✅ Filenames prevent collisions                             │
└──────────────────────────────────────────────────────────────┘
```

---

## Proof It Works

### Test Scenario

1. **Download in order:** Card 1, Card 0, Card 2
2. **Wait 5 minutes**
3. **Analyze in order:** Card 2, Card 0, Card 1

**Expected Result:**
- Card 1 AI analysis mentions methods from papers **11111 & 22222** ✅
- Card 0 AI analysis mentions methods from papers **12345 & 67890** ✅
- Card 2 AI analysis mentions methods from papers **33333 & 44444** ✅

**Why it works:**
- Each card's button has fixed index: `onclick="selectDataset(0)"`
- Each index points to fixed dataset: `currentResults[0].geo_id = "GSE123456"`
- Each dataset has own fulltext array: `currentResults[0].fulltext = [...]`
- Backend loops through that specific array: `for ft in dataset.fulltext:`

---

## Code Verification

### Frontend (dashboard_v2.html)

```javascript
// Line 1210: Download button
async function downloadPapersForDataset(index) {
    const dataset = currentResults[index];  // ✅ Get by index

    const enriched = await fetch('/enrich-fulltext', {
        body: JSON.stringify([dataset])  // ✅ Send with geo_id
    });

    currentResults[index] = enriched;  // ✅ Replace same index
}

// Line 1502: AI button
async function selectDataset(index) {
    const dataset = currentResults[index];  // ✅ Get by index

    await fetch('/analyze', {
        body: JSON.stringify({ datasets: [dataset] })  // ✅ Send with geo_id + fulltext
    });
}
```

### Backend (agents.py)

```python
# Line 403: Download endpoint
@router.post("/enrich-fulltext")
async def enrich_fulltext(datasets: List[DatasetResponse]):
    for dataset in datasets:  # ✅ Process each independently
        dataset.fulltext = []  # ✅ New array

        for pub in publications:  # ✅ Publications from THIS dataset's PMIDs
            parsed = parse_pdf(pub.pdf_path)
            dataset.fulltext.append(parsed)  # ✅ Append to THIS dataset

    return enriched_datasets

# Line 830: AI endpoint
@router.post("/analyze")
async def analyze_datasets(request: AIAnalysisRequest):
    for ds in request.datasets:  # ✅ Loop through input datasets
        for ft in ds.fulltext:  # ✅ Loop through THIS dataset's fulltext
            prompt += ft.methods  # ✅ Use THIS dataset's papers
            prompt += ft.results

    return ai_analysis(prompt)
```

---

## Summary

**Three guarantees prevent mixing:**

1. **Unique Identifiers:** `geo_id` (dataset) + `pmid` (paper) never change
2. **Object Isolation:** Each dataset has its own `fulltext` array instance
3. **Independent Processing:** Backend loops process one dataset at a time

**Result:** You can download and analyze in ANY order - the system always maps PDFs correctly to their datasets! 🎯

---

**Related Documentation:**
- Full details: `docs/DATA_FLOW_AND_MAPPING_MECHANISM.md`
- Visual diagrams: `docs/architecture/dataset_mapping_flow.md`
- Code locations:
  - Frontend: `omics_oracle_v2/api/static/dashboard_v2.html`
  - Backend: `omics_oracle_v2/api/routes/agents.py`
