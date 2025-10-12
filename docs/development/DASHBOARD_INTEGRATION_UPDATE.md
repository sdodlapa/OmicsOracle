# Dashboard Integration Update - Connect to Unified Search Pipeline

**Date:** October 12, 2025  
**Status:** NEEDS UPDATE  
**Priority:** HIGH

---

## Issue Identified

The dashboard (`omics_oracle_v2/lib/dashboard/app.py`) currently uses **PublicationSearchPipeline** which only searches publications (PubMed, Scholar).

**Problem:** It doesn't connect to the **UnifiedSearchPipeline** which provides:
- GEO dataset search
- GEO metadata retrieval
- GEO → Citation → PDF pipeline
- Complete integration with Phase 5 fulltext/normalization

---

## Current State

### Dashboard Location
```
omics_oracle_v2/lib/dashboard/
├── app.py                  # Main dashboard (NEEDS UPDATE)
├── components.py           # UI components
├── config.py               # Configuration
├── preferences.py          # User preferences
└── search_history.py       # Search history management
```

### Current Search Implementation (Lines 271-295)
```python
# Currently using PublicationSearchPipeline
from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig

pipeline = PublicationSearchPipeline(pipeline_config)
search_result = pipeline.search(query=query, max_results=params["max_results"])
```

**What's Missing:**
- ❌ No GEO dataset search
- ❌ No GEO metadata display
- ❌ No GEO → Citation pipeline
- ❌ No PDF/fulltext display for GEO datasets
- ❌ Not using UnifiedSearchPipeline

---

## Required Changes

### Change 1: Add UnifiedSearchPipeline Support

**File:** `omics_oracle_v2/lib/dashboard/app.py`

**Update `_execute_search()` method** (Line 271):

```python
def _execute_search(self, params: Dict[str, Any]) -> None:
    """Execute search with given parameters."""
    query = params["query"]

    # Add to session history
    if query not in st.session_state.search_history:
        st.session_state.search_history.append(query)

    # Show progress
    with st.spinner(f"Searching for: {query}..."):
        try:
            # Determine search type based on databases selected
            search_geo = "geo" in params["databases"]
            search_publications = "pubmed" in params["databases"] or "scholar" in params["databases"]

            results_data = {"publications": [], "geo_datasets": []}

            # === GEO SEARCH (NEW!) ===
            if search_geo:
                from omics_oracle_v2.lib.pipelines.unified_search_pipeline import (
                    OmicsSearchPipeline,
                    UnifiedSearchConfig,
                )

                # Configure unified search
                geo_config = UnifiedSearchConfig(
                    enable_geo_search=True,
                    enable_publication_search=False,
                    use_cache=True,
                    cache_ttl_seconds=3600,
                )

                # Create pipeline
                geo_pipeline = OmicsSearchPipeline(geo_config)

                # Execute search (ASYNC!)
                import asyncio

                search_start = datetime.now()
                geo_result = asyncio.run(
                    geo_pipeline.search(
                        query=query,
                        max_geo_results=params.get("max_results", 10),
                    )
                )
                search_end = datetime.now()
                execution_time = (search_end - search_start).total_seconds()

                # Process GEO results
                if geo_result.geo_datasets:
                    geo_dicts = []
                    for geo_metadata in geo_result.geo_datasets:
                        geo_dict = {
                            "geo_id": geo_metadata.geo_id,
                            "title": geo_metadata.title,
                            "summary": geo_metadata.summary,
                            "organism": geo_metadata.organism,
                            "samples": geo_metadata.sample_count,
                            "platform": geo_metadata.platform,
                            "pubmed_ids": geo_metadata.pubmed_ids,
                            "publication_date": geo_metadata.publication_date,
                            "type": geo_metadata.series_type,
                            "has_raw_data": geo_metadata.has_raw_data(),
                            "download_summary": geo_metadata.get_download_summary(),
                        }
                        geo_dicts.append(geo_dict)

                    results_data["geo_datasets"] = geo_dicts

                    st.info(f"Found {len(geo_dicts)} GEO datasets in {execution_time:.2f}s")

            # === PUBLICATION SEARCH (EXISTING) ===
            if search_publications:
                from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
                from omics_oracle_v2.lib.publications.config import PublicationSearchConfig

                # Create pipeline config
                pipeline_config = PublicationSearchConfig(
                    enable_pubmed="pubmed" in params["databases"],
                    enable_scholar="scholar" in params["databases"],
                    enable_citations=params.get("use_llm", False),
                    max_total_results=params["max_results"],
                )

                # Execute search
                pipeline = PublicationSearchPipeline(pipeline_config)

                search_start = datetime.now()
                search_result = pipeline.search(
                    query=query,
                    max_results=params["max_results"],
                )
                search_end = datetime.now()
                pub_exec_time = (search_end - search_start).total_seconds()

                # Convert to dictionaries
                results_dicts = []
                for search_res in search_result.publications:
                    pub = search_res.publication
                    pub_dict = {
                        "id": pub.pmid or pub.doi or pub.title,
                        "title": pub.title,
                        "abstract": pub.abstract or "",
                        "authors": pub.authors,
                        "journal": pub.journal,
                        "year": pub.publication_date.year if pub.publication_date else None,
                        "citations": pub.citations,
                        "source": pub.source.value,
                        "relevance_score": search_res.relevance_score,
                        "pmid": pub.pmid,
                        "doi": pub.doi,
                        "url": pub.url,
                    }
                    results_dicts.append(pub_dict)

                results_data["publications"] = results_dicts

                st.success(f"Found {len(results_dicts)} publications in {pub_exec_time:.2f}s")

            # Save to history
            record = SearchRecord(
                query=query,
                databases=params["databases"],
                year_range=params.get("year_range", (2000, 2024)),
                max_results=params["max_results"],
                timestamp=datetime.now().isoformat(),
                result_count=len(results_data["publications"]) + len(results_data["geo_datasets"]),
                execution_time=execution_time if search_geo else pub_exec_time,
                use_llm=params.get("use_llm", False),
            )
            self.history_manager.add_search(record)

            # Process and save results
            st.session_state.search_results = self._process_results(results_data, params)
            st.session_state.current_query = query

        except Exception as e:
            st.error(f"Search failed: {str(e)}")
            import traceback

            st.error(traceback.format_exc())
            st.session_state.search_results = None
```

### Change 2: Add GEO Dataset Database Option

**File:** `omics_oracle_v2/lib/dashboard/components.py`

**Update SearchPanel.render()** to add GEO option:

```python
# Add to database selection (around line 50-60 in components.py)
databases = st.multiselect(
    "Search Databases",
    options=["geo", "pubmed", "scholar"],  # Add 'geo'
    default=["geo", "pubmed"],  # Default to GEO + PubMed
    help="Select databases to search. GEO for datasets, PubMed/Scholar for publications",
)
```

### Change 3: Update Results Display for GEO Datasets

**File:** `omics_oracle_v2/lib/dashboard/components.py`

**Add to ResultsPanel.render():**

```python
def render(self, results: Dict[str, Any]) -> None:
    """Render search results with GEO datasets and publications."""
    
    # Display GEO datasets first (if any)
    geo_datasets = results.get("geo_datasets", [])
    if geo_datasets:
        st.subheader(f"🧬 GEO Datasets ({len(geo_datasets)})")
        
        for idx, dataset in enumerate(geo_datasets):
            with st.expander(
                f"**{dataset['geo_id']}**: {dataset['title'][:100]}...",
                expanded=(idx < 3)  # Expand first 3
            ):
                # Display metadata
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Organism", dataset.get("organism", "N/A"))
                with col2:
                    st.metric("Samples", dataset.get("samples", 0))
                with col3:
                    st.metric("Platform", dataset.get("platform", "N/A")[:20])
                with col4:
                    st.metric("Type", dataset.get("type", "N/A"))
                
                # Summary
                st.markdown("**Summary:**")
                st.write(dataset.get("summary", "No summary available")[:500])
                
                # PubMed IDs (links to publications)
                pmids = dataset.get("pubmed_ids", [])
                if pmids:
                    st.markdown("**Related Publications:**")
                    for pmid in pmids[:5]:  # Show first 5
                        st.markdown(f"- [PMID: {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
                
                # Download info
                if dataset.get("has_raw_data"):
                    st.info(f"📊 {dataset.get('download_summary', 'Raw data available')}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.button(
                        "View on GEO",
                        key=f"geo_{dataset['geo_id']}",
                        on_click=lambda: st.session_state.update(
                            {"open_url": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={dataset['geo_id']}"}
                        ),
                    )
                with col2:
                    if pmids:
                        st.button(
                            "Get Citations",
                            key=f"citations_{dataset['geo_id']}",
                            help="Find papers citing this dataset",
                        )
                with col3:
                    st.button(
                        "Download PDFs",
                        key=f"pdfs_{dataset['geo_id']}",
                        help="Download full-text PDFs for related publications",
                    )
        
        st.divider()
    
    # Display publications (existing code)
    publications = results.get("publications", [])
    if publications:
        st.subheader(f"📚 Publications ({len(publications)})")
        # ... rest of existing publication display code ...
```

### Change 4: Add GEO → Citation → PDF Pipeline Integration

**New method in `app.py`:**

```python
def _get_geo_citations_and_pdfs(self, geo_id: str) -> None:
    """Get citations and download PDFs for a GEO dataset.
    
    Args:
        geo_id: GEO series ID (e.g., "GSE123456")
    """
    with st.spinner(f"Finding citations and downloading PDFs for {geo_id}..."):
        try:
            from omics_oracle_v2.lib.pipelines.geo_citation_pipeline import (
                GEOCitationPipeline,
                GEOCitationConfig,
            )
            from pathlib import Path
            
            # Configure pipeline
            config = GEOCitationConfig(
                geo_max_results=1,  # Just this one dataset
                citation_max_results=50,
                use_citation_strategy=True,
                use_mention_strategy=True,
                enable_institutional=True,
                enable_unpaywall=True,
                download_pdfs=True,  # Download PDFs!
            )
            
            # Create pipeline
            pipeline = GEOCitationPipeline(config)
            
            # Run collection (ASYNC!)
            import asyncio
            result = asyncio.run(pipeline.collect_for_geo_ids([geo_id]))
            
            # Display results
            if result.collections:
                collection = result.collections[0]
                
                st.success(
                    f"✅ Found {len(collection.publications)} publications "
                    f"({collection.pdfs_downloaded} PDFs downloaded)"
                )
                
                # Show collection path
                st.info(f"📁 Collection saved to: `{collection.storage_path}`")
                
                # Display publications with PDF download links
                st.subheader("Publications & PDFs")
                for pub in collection.publications:
                    with st.expander(f"{pub.title[:80]}..."):
                        st.write(f"**PMID:** {pub.pmid}")
                        st.write(f"**DOI:** {pub.doi}")
                        
                        if pub.pdf_path:
                            pdf_path = Path(pub.pdf_path)
                            if pdf_path.exists():
                                # Offer PDF download
                                with open(pdf_path, "rb") as f:
                                    st.download_button(
                                        "📄 Download PDF",
                                        data=f.read(),
                                        file_name=pdf_path.name,
                                        mime="application/pdf",
                                    )
                        
                        # View fulltext (if cached)
                        if st.button(f"View Fulltext", key=f"fulltext_{pub.pmid}"):
                            self._show_fulltext(pub.pmid)
            
        except Exception as e:
            st.error(f"Failed to get citations/PDFs: {e}")
            import traceback
            st.error(traceback.format_exc())
```

### Change 5: Add Fulltext Viewer

**New method in `app.py`:**

```python
def _show_fulltext(self, publication_id: str) -> None:
    """Display normalized fulltext for a publication.
    
    Args:
        publication_id: Publication ID (PMID or PMC ID)
    """
    try:
        from omics_oracle_v2.lib.fulltext.parsed_cache import ParsedCache
        import asyncio
        
        cache = ParsedCache()
        
        # Get normalized content (Phase 5!)
        content = asyncio.run(cache.get_normalized(publication_id))
        
        if content:
            st.subheader(f"📖 Fulltext: {publication_id}")
            
            # Metadata
            metadata = content.get("metadata", {})
            st.caption(f"Format: {metadata.get('source_format', 'unknown')}")
            st.caption(f"Normalized: {metadata.get('normalized_at', 'N/A')}")
            
            # Text content
            text = content.get("text", {})
            
            # Title
            st.markdown(f"## {text.get('title', 'No title')}")
            
            # Abstract
            if text.get("abstract"):
                st.markdown("### Abstract")
                st.write(text["abstract"])
            
            # Sections
            sections = text.get("sections", {})
            if sections:
                st.markdown("### Full Text")
                tabs = st.tabs(list(sections.keys()))
                for i, (section_name, section_text) in enumerate(sections.items()):
                    with tabs[i]:
                        st.write(section_text)
            
            # Tables
            tables = content.get("tables", [])
            if tables:
                st.markdown(f"### Tables ({len(tables)})")
                for i, table in enumerate(tables):
                    with st.expander(f"Table {i+1}: {table.get('caption', 'No caption')}"):
                        st.text(table.get("text", "No content"))
            
            # Figures
            figures = content.get("figures", [])
            if figures:
                st.markdown(f"### Figures ({len(figures)})")
                for i, figure in enumerate(figures):
                    st.write(f"**Figure {i+1}:** {figure.get('caption', 'No caption')}")
        else:
            st.warning(f"No cached fulltext found for {publication_id}")
            
    except Exception as e:
        st.error(f"Failed to load fulltext: {e}")
```

---

## Updated Dashboard Architecture

### New Data Flow

```
User Query
    ↓
Dashboard SearchPanel
    ↓
┌─────────────────────┬─────────────────────┐
│                     │                     │
GEO Search            Publication Search
(UnifiedSearchPipeline) (PublicationSearchPipeline)
│                     │                     │
↓                     ↓                     
GEO Datasets          Publications
    ↓
Click "Get Citations"
    ↓
GEOCitationPipeline
    ↓
Citations + PDFs Downloaded
    ↓
Display with Download Buttons
    ↓
Click "View Fulltext"
    ↓
ParsedCache.get_normalized()
    ↓
Display Normalized Content (Phase 5!)
```

### New Features

1. **GEO Dataset Search** - Search GEO database directly from dashboard
2. **GEO Metadata Display** - Show organism, samples, platform, etc.
3. **Citation Discovery** - One-click to find all citing papers
4. **PDF Downloads** - Automatic PDF download for citations
5. **Fulltext Viewer** - View normalized fulltext (JATS/PDF → unified format)
6. **Collection Management** - Saved to `data/geo_citation_collections/{geo_id}/`

---

## Implementation Steps

### Step 1: Update Search Panel (components.py)
```bash
# Add 'geo' to database options
# Update help text to explain GEO search
```

### Step 2: Update App Search Method (app.py)
```bash
# Add UnifiedSearchPipeline import
# Add GEO search logic
# Add async search execution
# Process GEO results alongside publications
```

### Step 3: Update Results Display (components.py)
```bash
# Add GEO dataset cards
# Add "Get Citations" button
# Add "Download PDFs" button
# Add "View Fulltext" button
```

### Step 4: Add Citation/PDF Methods (app.py)
```bash
# Add _get_geo_citations_and_pdfs()
# Add _show_fulltext()
# Add PDF download buttons
```

### Step 5: Update Session State (app.py)
```bash
# Add geo_collections to session_state
# Add selected_geo_id to session_state
# Add fulltext_viewer state
```

### Step 6: Test Integration
```bash
# Test GEO search
# Test citation discovery
# Test PDF download
# Test fulltext viewing
```

---

## Testing Checklist

- [ ] GEO search returns datasets
- [ ] GEO metadata displays correctly
- [ ] "Get Citations" button works
- [ ] PDFs download successfully
- [ ] Fulltext viewer shows normalized content
- [ ] Collections saved to correct directory
- [ ] Can switch between GEO and publication search
- [ ] Both search types work together
- [ ] Session history tracks both types
- [ ] Export includes both GEO and publications

---

## Files to Modify

1. **`omics_oracle_v2/lib/dashboard/app.py`** (MAIN)
   - Update `_execute_search()` to support UnifiedSearchPipeline
   - Add `_get_geo_citations_and_pdfs()`
   - Add `_show_fulltext()`
   - Update `_process_results()` to handle GEO datasets

2. **`omics_oracle_v2/lib/dashboard/components.py`**
   - Update `SearchPanel.render()` to add 'geo' database option
   - Update `ResultsPanel.render()` to display GEO datasets
   - Add GEO-specific UI components

3. **`omics_oracle_v2/lib/dashboard/config.py`**
   - Add `enable_geo_search: bool = True`
   - Add `enable_fulltext_viewer: bool = True`

---

## Benefits After Update

### For Users:
1. **One-stop search** - GEO datasets + publications in one interface
2. **Citation discovery** - Find all papers related to a GEO dataset
3. **Instant PDFs** - One-click PDF download for all citations
4. **Fulltext viewing** - Read papers directly in dashboard (no PDF reader needed)
5. **Organized collections** - All data saved together by GEO ID

### For Developers:
1. **Unified pipeline** - Consistent search interface
2. **Phase 5 integration** - Uses normalized fulltext
3. **Future-proof** - Ready for vector search, embeddings, RAG
4. **Maintainable** - Single pipeline to maintain

---

## Example Use Case

**User workflow:**

1. Search for "diabetes gene expression" with GEO database selected
2. Dashboard shows 10 GEO datasets with metadata
3. Click "Get Citations" on GSE123456
4. Dashboard finds 25 citing papers, downloads 20 PDFs
5. Click "View Fulltext" on any paper
6. Dashboard shows normalized fulltext with sections, tables, figures
7. Click "Download PDF" to save PDF locally
8. All data saved to `data/geo_citation_collections/GSE123456/`

**Time saved:** 
- Manual search: ~30 minutes
- With dashboard: ~2 minutes

---

## Next Steps

1. **Immediate:** Update `app.py` with UnifiedSearchPipeline integration
2. **Short-term:** Add GEO dataset display to ResultsPanel
3. **Medium-term:** Add citation discovery and PDF download
4. **Long-term:** Add fulltext viewer and collection management

---

## Notes

- Dashboard is using Streamlit (already installed)
- All required pipelines already implemented (Phase 4 complete)
- Phase 5 normalization ready for fulltext viewing
- Just needs to wire everything together!

**Estimated time:** 2-3 hours for complete integration

---

## Questions?

- How to handle async pipeline calls in Streamlit? → Use `asyncio.run()`
- Where to save downloaded PDFs? → `data/geo_citation_collections/{geo_id}/pdfs/`
- How to display normalized fulltext? → Use ParsedCache.get_normalized()
- Should we add search filters? → Yes, add organism, sample count, date range filters
