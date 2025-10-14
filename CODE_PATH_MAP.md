# ACTUAL CODE PATH: GEO Search → PDF Download

## THE REAL EXECUTION PATH (Not Documentation, Actual Code)

### 1. Frontend Click
**File**: `omics_oracle_v2/api/static/dashboard_v2.html`
**Line**: 1210
```javascript
const response = await authenticatedFetch('http://localhost:8000/api/agents/enrich-fulltext', {
    method: 'POST',
    body: JSON.stringify([dataset]),
});
```

### 2. API Endpoint
**File**: `omics_oracle_v2/api/routes/agents.py`
**Line**: 323-350
```python
@router.post("/enrich-fulltext")
async def enrich_fulltext(
    datasets: List[DatasetResponse],
    include_citing_papers: bool = Query(default=True),
    ...
):
```

### 3. Citation Discovery Initialization
**File**: `omics_oracle_v2/api/routes/agents.py`
**Line**: 418-420
```python
if include_citing_papers:
    citation_discovery = GEOCitationDiscovery()
```

### 4. Citation Discovery Class
**File**: `omics_oracle_v2/lib/citations/discovery/geo_discovery.py`
**Lines**: 45-52 (JUST FIXED)
```python
def __init__(self, ...):
    if citation_finder is None:
        from omics_oracle_v2.lib.search_engines.citations.openalex import OpenAlexClient, OpenAlexConfig
        openalex_config = OpenAlexConfig(email=os.getenv("NCBI_EMAIL"), enable=True)
        openalex_client = OpenAlexClient(config=openalex_config)
        self.citation_finder = CitationFinder(openalex_client=openalex_client)
```

### 5. Find Citing Papers
**File**: `omics_oracle_v2/lib/citations/discovery/geo_discovery.py`  
**Line**: 131-148 (JUST FIXED)
```python
async def _find_via_citation(self, pmid: str, max_results: int):
    original_pub = self.pubmed_client.fetch_by_id(pmid)  # Get DOI
    citing_papers = self.citation_finder.find_citing_papers(publication=original_pub, ...)
    return citing_papers
```

### 6. OpenAlex Get Citing Papers
**File**: `omics_oracle_v2/lib/search_engines/citations/openalex.py`
**Line**: 215-263
```python
def get_citing_papers(self, doi=None, ...):
    work = self.get_work_by_doi(doi)
    openalex_id = work["id"]
    # Get citing works
    url = f"{self.config.api_url}/works"
    params = {"filter": f"cites:{openalex_id}", ...}
    data = self._make_request(url, params=params)
    for work in data["results"]:
        pub = self._convert_work_to_publication(work)  # EXTRACTS PMID HERE
        citing_papers.append(pub)
    return citing_papers
```

### 7. Convert OpenAlex Work to Publication
**File**: `omics_oracle_v2/lib/search_engines/citations/openalex.py`
**Line**: 372-391 (JUST FIXED)
```python
def _convert_work_to_publication(self, work: Dict):
    # Extract PMID from ids object
    ids = work.get("ids", {})
    pmid_url = ids.get("pmid")
    if pmid_url:
        pmid = pmid_url.split("/")[-1]
    
    pub = Publication(
        pmid=pmid,  # NOW EXTRACTED!
        doi=doi,
        title=title,
        ...
    )
    return pub
```

### 8. Publication Model
**File**: `omics_oracle_v2/lib/search_engines/citations/models.py`
**Line**: 28-110 (JUST FIXED)
```python
class Publication(BaseModel):
    pmid: Optional[str] = None
    doi: Optional[str] = None
    paper_type: Optional[str] = None  # JUST ADDED
    
    @property
    def id(self) -> str:  # JUST ADDED
        return self.primary_id
    
    @property
    def primary_id(self) -> str:
        return self.pmid or self.pmcid or self.doi or f"unknown_{hash(self.title)}"
```

### 9. PDF Downloading
**File**: `omics_oracle_v2/api/routes/agents.py`
**Line**: 500-600
```python
# Download PDFs
for pub in papers_to_download["citing"]:
    result = await pdf_downloader.download_with_fallback(publication=pub, ...)
```

### 10. PDF Parsing
**File**: `omics_oracle_v2/lib/enrichment/fulltext/manager.py`
**Line**: 1122
```python
from omics_oracle_v2.lib.enrichment.fulltext.pdf_parser import PDFExtractor
parsed = PDFExtractor.extract_text(pdf_path)
```

### 11. PDF Parser
**File**: `omics_oracle_v2/lib/enrichment/fulltext/pdf_parser.py` (JUST CREATED)
```python
class PDFExtractor:
    @staticmethod
    def extract_text(pdf_path: Path):
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text())
        return {"full_text": "\n\n".join(text_parts), ...}
```

---

## FILES INVOLVED (11 Total)

1. ✅ `omics_oracle_v2/api/static/dashboard_v2.html` - Frontend
2. ✅ `omics_oracle_v2/api/routes/agents.py` - API endpoint + orchestration
3. ✅ `omics_oracle_v2/lib/citations/discovery/geo_discovery.py` - Citation discovery logic
4. ✅ `omics_oracle_v2/lib/citations/discovery/finder.py` - CitationFinder wrapper
5. ✅ `omics_oracle_v2/lib/search_engines/citations/openalex.py` - OpenAlex API client
6. ✅ `omics_oracle_v2/lib/search_engines/citations/models.py` - Publication model
7. ✅ `omics_oracle_v2/lib/search_engines/citations/pubmed.py` - PubMed client
8. ✅ `omics_oracle_v2/lib/enrichment/fulltext/manager.py` - FullTextManager
9. ✅ `omics_oracle_v2/lib/enrichment/fulltext/download_manager.py` - PDFDownloadManager
10. ✅ `omics_oracle_v2/lib/enrichment/fulltext/pdf_parser.py` - PDF text extraction
11. ✅ `omics_oracle_v2/lib/search_engines/geo/models.py` - GEOSeriesMetadata

---

## FIXES APPLIED TODAY

1. **OpenAlexConfig initialization** (geo_discovery.py) - Fixed bare email parameter
2. **PubMed method name** (geo_discovery.py) - fetch_by_id instead of fetch_details
3. **Publication.id property** (models.py) - Added alias to primary_id
4. **PMID extraction from OpenAlex** (openalex.py) - Extract from ids object
5. **PDF parser creation** (pdf_parser.py) - Created missing module
6. **GEO ID in logs** (agents.py) - Added [GSE...] prefix

---

## NO REDUNDANT PATHS FOUND

There is **ONE single code path** from frontend → backend → citation discovery → PDF download.

No parallel/duplicate implementations detected.

The issue was simply **missing implementations** (pdf_parser.py) and **bugs in the actual code** (not using wrong files).
