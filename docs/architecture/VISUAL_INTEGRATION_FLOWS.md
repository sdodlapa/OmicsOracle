# Visual Integration Flowcharts
**Date:** October 12, 2025  
**Purpose:** Mermaid diagrams for end-to-end integration flow

## 1. Complete User Journey (Sequence Diagram)

```mermaid
sequenceDiagram
    actor User
    participant Dashboard as Dashboard UI
    participant SearchAgent as SearchAgent
    participant UnifiedPipeline as UnifiedSearchPipeline
    participant GEOClient as GEO E-utilities
    participant CitePipeline as GEOCitationPipeline
    participant PubMed as PubMed API
    participant PDFDownload as PDF Downloaders
    participant Parser as Content Parser
    participant Cache as ParsedCache
    participant Storage as File Storage

    %% PHASE 1: Search
    User->>Dashboard: Enter "diabetes RNA-seq"
    Dashboard->>SearchAgent: execute(search_input)
    SearchAgent->>UnifiedPipeline: search(query="diabetes RNA-seq")
    
    UnifiedPipeline->>GEOClient: esearch(query)
    GEOClient-->>UnifiedPipeline: GEO IDs [GSE123456, ...]
    
    UnifiedPipeline->>GEOClient: fetch_metadata(parallel)
    GEOClient-->>UnifiedPipeline: Metadata + PMIDs
    
    UnifiedPipeline-->>SearchAgent: RankedDatasets
    SearchAgent-->>Dashboard: SearchOutput
    
    %% PHASE 2: Display Results
    Dashboard->>User: Display GEO cards<br/>(metadata + PMID count)
    
    Note over User,Dashboard: User sees:<br/>GSE123456: "Diabetes..."<br/>📚 2 publications linked
    
    %% PHASE 3: Citation Discovery
    User->>Dashboard: Click "Get Citations"
    Dashboard->>PubMed: efetch(pmids=[12345678, 87654321])
    PubMed-->>Dashboard: Citation metadata
    Dashboard->>Storage: Cache citations.json
    Dashboard->>User: Display citation list<br/>(titles, authors, DOIs)
    
    %% PHASE 4: PDF Download
    User->>Dashboard: Click "Download PDFs"
    Dashboard->>CitePipeline: discover_and_download(geo_id, pmids)
    
    loop For each PMID
        CitePipeline->>PDFDownload: Try Unpaywall
        alt PDF found
            PDFDownload-->>CitePipeline: PDF bytes
        else Not found
            CitePipeline->>PDFDownload: Try PMC
            PDFDownload-->>CitePipeline: PDF bytes or fail
        end
        
        CitePipeline->>Storage: Save PDF<br/>data/pdfs/GSE123456/PMID_*.pdf
        
        CitePipeline->>Parser: parse(pdf_bytes)
        Parser-->>CitePipeline: Parsed content (JATS/PDF format)
        
        CitePipeline->>Cache: store_parsed(pmid, content)
        Cache->>Storage: Save JSON<br/>data/fulltext/parsed/PMID_*.json
    end
    
    CitePipeline-->>Dashboard: DownloadResult<br/>(status, counts)
    Dashboard->>User: Show download status<br/>✓ 2/2 PDFs downloaded
    
    %% PHASE 5: Fulltext Viewing
    User->>Dashboard: Click "View Fulltext"
    Dashboard->>Cache: get_normalized(pmid)
    Cache->>Storage: Load PMID_*.json
    Cache->>Cache: Normalize format<br/>(JATS/PDF → Unified)
    Cache-->>Dashboard: NormalizedContent<br/>(sections, tables, figures)
    
    Dashboard->>User: Display fulltext<br/>(expandable sections)
```

## 2. Data Flow Architecture

```mermaid
graph TB
    subgraph Frontend["🖥️ FRONTEND (Streamlit Dashboard)"]
        SearchBox[Search Input Box]
        GEOCard[GEO Dataset Card]
        CitationList[Citation List]
        PDFViewer[PDF Viewer]
        FulltextViewer[Fulltext Viewer]
    end
    
    subgraph Agents["🤖 AGENTS LAYER"]
        QueryAgent[QueryAgent<br/>NER + Intent]
        SearchAgent[SearchAgent<br/>GEO Search]
    end
    
    subgraph Pipelines["⚙️ PIPELINES LAYER"]
        UnifiedPipeline[UnifiedSearchPipeline<br/>GEO + Publications]
        CitationPipeline[GEOCitationPipeline<br/>Discover + Download]
    end
    
    subgraph Services["🌐 EXTERNAL SERVICES"]
        NCBI[NCBI E-utilities<br/>GEO Database]
        PubMed[PubMed API<br/>Citation Metadata]
        Unpaywall[Unpaywall API<br/>Open Access PDFs]
        PMC[PMC API<br/>PubMed Central]
    end
    
    subgraph Storage["💾 LOCAL STORAGE"]
        PDFStorage[(PDFs<br/>data/pdfs/GSE*/)]
        FulltextStorage[(Fulltext<br/>data/fulltext/parsed/)]
        CacheStorage[(Cache<br/>data/cache/)]
        CollectionStorage[(Collections<br/>data/geo_citation_collections/)]
    end
    
    subgraph Processing["🔧 PROCESSING"]
        Parser[Content Parser<br/>JATS/PDF/LaTeX]
        Normalizer[Content Normalizer<br/>Phase 5]
        ParsedCache[ParsedCache<br/>Smart Caching]
    end
    
    %% User interactions
    SearchBox -->|1. Query| QueryAgent
    QueryAgent -->|2. Optimized Query| SearchAgent
    SearchAgent -->|3. Search| UnifiedPipeline
    
    %% Search flow
    UnifiedPipeline -->|4. Query| NCBI
    NCBI -->|5. GEO Metadata + PMIDs| UnifiedPipeline
    UnifiedPipeline -->|6. Results| GEOCard
    
    %% Citation discovery
    GEOCard -->|7. User clicks<br/>"Get Citations"| PubMed
    PubMed -->|8. Citation Metadata| CitationList
    CitationList -->|9. Cache| CollectionStorage
    
    %% PDF download
    CitationList -->|10. User clicks<br/>"Download PDFs"| CitationPipeline
    CitationPipeline -->|11. Request PDFs| Unpaywall
    CitationPipeline -->|12. Fallback| PMC
    Unpaywall -->|13. PDF bytes| CitationPipeline
    PMC -->|13. PDF bytes| CitationPipeline
    
    %% Parsing and storage
    CitationPipeline -->|14. Parse| Parser
    Parser -->|15. Parsed content| Normalizer
    Normalizer -->|16. Normalized| ParsedCache
    ParsedCache -->|17. Store| PDFStorage
    ParsedCache -->|18. Store| FulltextStorage
    
    %% Fulltext viewing
    FulltextViewer -->|19. User clicks<br/>"View Fulltext"| ParsedCache
    ParsedCache -->|20. Load| FulltextStorage
    ParsedCache -->|21. Return| FulltextViewer
    
    %% Caching
    UnifiedPipeline -.->|Cache hits| CacheStorage
    ParsedCache -.->|Cache normalized| CacheStorage
    
    style Frontend fill:#e1f5ff
    style Agents fill:#fff4e1
    style Pipelines fill:#f0e1ff
    style Services fill:#e1ffe1
    style Storage fill:#ffe1e1
    style Processing fill:#ffe1f5
```

## 3. State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> SearchInput: User enters query
    
    SearchInput --> Searching: Click "Search"
    Searching --> ResultsDisplayed: Search complete
    
    ResultsDisplayed --> CitationLoading: Click "Get Citations"
    CitationLoading --> CitationsDisplayed: Citations fetched
    
    CitationsDisplayed --> PDFDownloading: Click "Download PDFs"
    PDFDownloading --> PDFsReady: All PDFs downloaded
    
    PDFsReady --> FulltextViewing: Click "View Fulltext"
    FulltextViewing --> FulltextDisplayed: Content loaded
    
    FulltextDisplayed --> SearchInput: New search
    ResultsDisplayed --> SearchInput: New search
    CitationsDisplayed --> SearchInput: New search
    
    state Searching {
        [*] --> QueryOptimization
        QueryOptimization --> GEOSearch
        GEOSearch --> MetadataFetch
        MetadataFetch --> Ranking
        Ranking --> [*]
    }
    
    state PDFDownloading {
        [*] --> TryUnpaywall
        TryUnpaywall --> PDFFound: Success
        TryUnpaywall --> TryPMC: Failed
        TryPMC --> PDFFound: Success
        TryPMC --> TryPublisher: Failed
        TryPublisher --> PDFFound: Success
        TryPublisher --> PDFFailed: All failed
        PDFFound --> ParsePDF
        ParsePDF --> NormalizeContent
        NormalizeContent --> StoreFulltext
        StoreFulltext --> [*]
        PDFFailed --> [*]
    }
```

## 4. Component Interaction Diagram

```mermaid
graph LR
    subgraph UI["Dashboard UI Components"]
        SearchPanel[SearchPanel]
        ResultsPanel[ResultsPanel]
        GEOCard[GEODatasetCard]
        CitationCard[CitationCard]
        FulltextPanel[FulltextPanel]
    end
    
    subgraph State["Session State"]
        SearchState[search_results:<br/>List[GEODataset]]
        DatasetState[dataset_state:<br/>Dict[geo_id, State]]
        FileMap[file_map:<br/>Dict[geo_id, Paths]]
    end
    
    subgraph Backend["Backend Services"]
        SearchSvc[SearchAgent]
        CiteSvc[Citation Service]
        PDFSvc[PDF Download Service]
        CacheSvc[ParsedCache]
    end
    
    SearchPanel -->|search query| SearchSvc
    SearchSvc -->|results| SearchState
    SearchState -->|render| ResultsPanel
    ResultsPanel -->|for each| GEOCard
    
    GEOCard -->|get citations| CiteSvc
    CiteSvc -->|update| DatasetState
    DatasetState -->|render| CitationCard
    
    CitationCard -->|download PDFs| PDFSvc
    PDFSvc -->|update| FileMap
    FileMap -->|load| CacheSvc
    CacheSvc -->|display| FulltextPanel
```

## 5. File Organization Flow

```mermaid
graph TD
    Search[GEO Search<br/>GSE123456]
    
    Search -->|Returns| Metadata[GEO Metadata<br/>+ PMIDs: 12345678, 87654321]
    
    Metadata -->|Creates| GEODir[data/pdfs/GSE123456/]
    Metadata -->|Creates| CollDir[data/geo_citation_collections/GSE123456/]
    
    GEODir -->|Stores| PDF1[PMID_12345678.pdf]
    GEODir -->|Stores| PDF2[PMID_87654321.pdf]
    
    CollDir -->|Stores| Citations[citations.json]
    CollDir -->|Stores| DownloadStatus[download_status.json]
    
    PDF1 -->|Parsed to| Fulltext1[data/fulltext/parsed/<br/>PMID_12345678.json]
    PDF2 -->|Parsed to| Fulltext2[data/fulltext/parsed/<br/>PMID_87654321.json]
    
    Fulltext1 -->|Normalized to| Norm1[PMID_12345678_normalized.json]
    Fulltext2 -->|Normalized to| Norm2[PMID_87654321_normalized.json]
    
    style Search fill:#e1f5ff
    style Metadata fill:#fff4e1
    style GEODir fill:#f0e1ff
    style CollDir fill:#f0e1ff
    style PDF1 fill:#ffe1e1
    style PDF2 fill:#ffe1e1
    style Fulltext1 fill:#e1ffe1
    style Fulltext2 fill:#e1ffe1
    style Norm1 fill:#ffe1f5
    style Norm2 fill:#ffe1f5
```

## 6. Button Click Flow

```mermaid
flowchart TD
    Start([User sees GEO result])
    
    Start --> ShowBasic[Display Basic Info:<br/>- GEO ID<br/>- Title<br/>- Organism<br/>- Sample count<br/>- PMID count]
    
    ShowBasic --> HasPMIDs{Has PMIDs?}
    
    HasPMIDs -->|Yes| ShowGetCite[Show button:<br/>'Get Citations']
    HasPMIDs -->|No| End1([No citations available])
    
    ShowGetCite --> ClickCite{User clicks?}
    ClickCite -->|No| Wait1[Wait...]
    Wait1 --> ClickCite
    
    ClickCite -->|Yes| CheckCache{Citations<br/>cached?}
    
    CheckCache -->|Yes| LoadCache[Load from:<br/>data/geo_citation_collections/<br/>GSE*/citations.json]
    CheckCache -->|No| FetchPubMed[Fetch from PubMed API]
    
    FetchPubMed --> SaveCache[Save to cache]
    SaveCache --> DisplayCite
    LoadCache --> DisplayCite[Display citations:<br/>- Title<br/>- Authors<br/>- Journal<br/>- DOI]
    
    DisplayCite --> ShowDownload[Show button:<br/>'Download PDFs']
    
    ShowDownload --> ClickDownload{User clicks?}
    ClickDownload -->|No| Wait2[Wait...]
    Wait2 --> ClickDownload
    
    ClickDownload -->|Yes| StartDownload[Start GEOCitationPipeline]
    
    StartDownload --> ForEachPMID[For each PMID]
    
    ForEachPMID --> TryUnpaywall{Try Unpaywall}
    TryUnpaywall -->|Found| DownloadPDF[Download PDF]
    TryUnpaywall -->|Not found| TryPMC{Try PMC}
    TryPMC -->|Found| DownloadPDF
    TryPMC -->|Not found| Failed[Mark as failed]
    
    DownloadPDF --> ParsePDF[Parse PDF to text]
    ParsePDF --> Normalize[Normalize content]
    Normalize --> SaveFiles[Save:<br/>- data/pdfs/GSE*/<br/>- data/fulltext/parsed/]
    
    SaveFiles --> NextPMID{More PMIDs?}
    NextPMID -->|Yes| ForEachPMID
    NextPMID -->|No| ShowStatus[Show download status:<br/>✓ X/Y PDFs downloaded]
    
    Failed --> NextPMID
    
    ShowStatus --> ShowFulltext[Show button:<br/>'View Fulltext']
    
    ShowFulltext --> ClickFulltext{User clicks?}
    ClickFulltext -->|No| Wait3[Wait...]
    Wait3 --> ClickFulltext
    
    ClickFulltext -->|Yes| LoadFulltext[Load normalized content<br/>from ParsedCache]
    
    LoadFulltext --> DisplaySections[Display sections:<br/>- Abstract<br/>- Introduction<br/>- Methods<br/>- Results<br/>- Discussion]
    
    DisplaySections --> DisplayTables[Display tables<br/>as dataframes]
    
    DisplayTables --> DisplayFigures[Display figure<br/>captions]
    
    DisplayFigures --> End2([User can read fulltext])
    
    style ShowBasic fill:#e1f5ff
    style DisplayCite fill:#fff4e1
    style ShowStatus fill:#f0e1ff
    style DisplaySections fill:#e1ffe1
    style End2 fill:#ffe1f5
```

## 7. Error Handling Flow

```mermaid
flowchart TD
    Action[User Action]
    
    Action --> Try{Try operation}
    
    Try -->|Get Citations| FetchCite[Fetch from PubMed]
    Try -->|Download PDFs| DownloadPDF[Download PDFs]
    Try -->|View Fulltext| LoadFulltext[Load fulltext]
    
    FetchCite --> CiteError{Error?}
    CiteError -->|Network error| ShowNetError[Show: Check connection]
    CiteError -->|API error| ShowAPIError[Show: Try again later]
    CiteError -->|Success| CiteSuccess[Display citations]
    
    DownloadPDF --> PDFError{Error?}
    PDFError -->|PDF not found| ShowNotFound[Show: PDF not available<br/>Try other sources]
    PDFError -->|Download failed| ShowDownFail[Show: Download failed<br/>Retry?]
    PDFError -->|Parse failed| ShowParseFail[Show: Could not parse PDF]
    PDFError -->|Success| PDFSuccess[Show: Downloaded successfully]
    
    LoadFulltext --> FullError{Error?}
    FullError -->|Not found| ShowNoFull[Show: Fulltext not available<br/>Download PDF first]
    FullError -->|Cache error| ShowCacheError[Show: Cache error<br/>Retry download]
    FullError -->|Success| FullSuccess[Display fulltext]
    
    ShowNetError --> Retry1{User retry?}
    ShowAPIError --> Retry1
    ShowNotFound --> TryAlternative[Try alternative sources]
    ShowDownFail --> Retry2{User retry?}
    ShowParseFail --> ShowRaw[Offer: View PDF directly]
    ShowNoFull --> SuggestDownload[Suggest: Download PDF]
    ShowCacheError --> Retry3{User retry?}
    
    Retry1 -->|Yes| FetchCite
    Retry1 -->|No| End1([Give up])
    Retry2 -->|Yes| DownloadPDF
    Retry2 -->|No| End1
    Retry3 -->|Yes| LoadFulltext
    Retry3 -->|No| End1
    
    CiteSuccess --> End2([Success])
    PDFSuccess --> End2
    FullSuccess --> End2
    TryAlternative --> End2
    ShowRaw --> End2
    SuggestDownload --> End2
```

---

## 8. How to Use These Diagrams

### In Documentation
Copy the Mermaid code blocks into:
- GitHub README (renders automatically)
- VS Code (with Mermaid extension)
- Online Mermaid Live Editor (https://mermaid.live)

### In Presentations
- Export as PNG/SVG from Mermaid Live
- Include in slides or technical docs

### For Development
- Use as reference while implementing
- Share with team for alignment
- Update as implementation evolves

---

## Quick Reference

### Key Files to Modify
1. `omics_oracle_v2/lib/dashboard/app.py` - Main dashboard logic
2. `omics_oracle_v2/lib/dashboard/components.py` - UI components
3. `omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py` - PDF download (already exists)
4. `omics_oracle_v2/lib/fulltext/cache.py` - Fulltext caching (already exists)

### Key Data Structures
1. **GEODatasetResult** - Search result with metadata + PMIDs
2. **Citation** - Citation metadata (title, authors, DOI)
3. **DownloadResult** - PDF download status + counts
4. **NormalizedContent** - Parsed fulltext in unified format

### Key Integration Points
1. **SearchAgent → Dashboard** - Pass GEO results with PMIDs
2. **Dashboard → GEOCitationPipeline** - Download PDFs on demand
3. **Dashboard → ParsedCache** - Retrieve normalized fulltext
4. **Session State** - Track per-dataset state (citations loaded, PDFs downloaded)
