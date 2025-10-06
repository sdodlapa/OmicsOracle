# 🔬 Advanced Text Extraction & Visualization Modules Plan

**Date**: December 28, 2024  
**Status**: Strategic Planning for Future Development  
**Priority**: High - Next Phase Development After Interface Consolidation  

---

## 📋 **Executive Overview**

This document outlines detailed implementation plans for four advanced modules that will transform OmicsOracle into a comprehensive biomedical research intelligence platform. These modules focus on full-text analysis, publication tracking, statistical extraction, and advanced visualization capabilities.

---

## 🗂️ **Module 1: Full-Text Publication Extraction System**

### **1.1 System Architecture**

**Core Components**:
```python
src/omics_oracle/text_extraction/
├── __init__.py
├── publication_fetcher.py     # Main orchestrator
├── ncbi_pubmed_client.py     # PubMed API integration
├── doi_resolver.py           # DOI to full-text mapping
├── pdf_processor.py          # PDF text extraction
├── html_scraper.py           # Web-based text extraction
├── text_preprocessor.py      # Text cleaning and normalization
├── storage_manager.py        # Extracted text storage
└── quality_validator.py      # Text quality assessment
```

### **1.2 Technical Implementation**

**Publication Discovery Pipeline**:
```python
class PublicationFetcher:
    """Orchestrates full-text extraction for GEO datasets"""
    
    async def extract_publication_info(self, geo_id: str) -> PublicationInfo:
        """Extract publication details from GEO dataset"""
        # 1. Get GEO metadata
        geo_data = await self.geo_client.get_dataset_info(geo_id)
        
        # 2. Extract publication references
        pub_refs = self.extract_publication_references(geo_data)
        
        # 3. Resolve DOIs and PMIDs
        resolved_refs = await self.resolve_publication_ids(pub_refs)
        
        return PublicationInfo(
            primary_publication=resolved_refs.primary,
            related_publications=resolved_refs.related
        )
    
    async def fetch_full_text(self, publication: Publication) -> FullTextContent:
        """Fetch full text using multiple strategies"""
        strategies = [
            self.try_pubmed_central,
            self.try_doi_resolution,
            self.try_publisher_api,
            self.try_web_scraping
        ]
        
        for strategy in strategies:
            try:
                content = await strategy(publication)
                if self.validate_content_quality(content):
                    return content
            except Exception as e:
                self.logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                continue
                
        raise NoFullTextAvailableError(f"No full text found for {publication.id}")
```

**Multi-Source Text Extraction**:
```python
class MultiSourceTextExtractor:
    """Handles various text extraction methods"""
    
    async def extract_from_pmc(self, pmc_id: str) -> TextContent:
        """Extract from PubMed Central"""
        pmc_data = await self.pmc_client.get_full_text(pmc_id)
        return TextContent(
            title=pmc_data.title,
            abstract=pmc_data.abstract,
            full_text=pmc_data.body,
            figures=pmc_data.figures,
            tables=pmc_data.tables,
            supplementary=pmc_data.supplementary_files
        )
    
    async def extract_from_pdf(self, pdf_url: str) -> TextContent:
        """Extract text from PDF using multiple engines"""
        extractors = [
            PyMuPDFExtractor(),
            PDFPlumberExtractor(),
            TikaExtractor()
        ]
        
        best_content = None
        best_score = 0
        
        for extractor in extractors:
            content = await extractor.extract(pdf_url)
            score = self.calculate_extraction_quality(content)
            
            if score > best_score:
                best_content = content
                best_score = score
                
        return best_content
```

### **1.3 Data Models**

```python
@dataclass
class PublicationInfo:
    """Complete publication information"""
    pmid: Optional[str]
    pmc_id: Optional[str]
    doi: Optional[str]
    title: str
    authors: List[str]
    journal: str
    publication_date: datetime
    abstract: str
    keywords: List[str]
    mesh_terms: List[str]

@dataclass
class FullTextContent:
    """Extracted full text with structured sections"""
    publication_info: PublicationInfo
    sections: Dict[str, str]  # Methods, Results, Discussion, etc.
    figures: List[FigureContent]
    tables: List[TableContent]
    supplementary_files: List[SupplementaryFile]
    extraction_metadata: ExtractionMetadata
    quality_score: float
    
@dataclass
class ExtractionMetadata:
    """Metadata about the extraction process"""
    extraction_method: str
    extraction_timestamp: datetime
    confidence_score: float
    processing_time_seconds: float
    source_url: str
    errors_encountered: List[str]
```

### **1.4 Implementation Timeline**

**Phase 1 (Weeks 1-2): Foundation**
- [ ] Implement PubMed/PMC API integration
- [ ] Create DOI resolution system
- [ ] Basic PDF text extraction
- [ ] Storage schema design

**Phase 2 (Weeks 3-4): Enhancement**
- [ ] Multi-strategy text extraction
- [ ] Quality assessment and validation
- [ ] Error handling and retry logic
- [ ] Caching and performance optimization

**Phase 3 (Weeks 5-6): Integration**
- [ ] Integration with existing GEO system
- [ ] API endpoints for text retrieval
- [ ] Background processing queue
- [ ] Monitoring and logging

---

## 📊 **Module 2: Related Publications Discovery System**

### **2.1 System Architecture**

```python
src/omics_oracle/publication_discovery/
├── __init__.py
├── citation_tracker.py       # Citation analysis
├── dataset_usage_finder.py   # Find papers using dataset
├── ml_project_detector.py    # ML/bioinformatics focus detection
├── semantic_similarity.py    # Content similarity analysis
├── knowledge_graph.py        # Publication relationships
├── supplementary_analyzer.py # Supplementary file analysis
└── recommendation_engine.py  # Related work suggestions
```

### **2.2 Discovery Strategies**

**Citation-Based Discovery**:
```python
class CitationTracker:
    """Track citations and references"""
    
    async def find_citing_papers(self, geo_id: str) -> List[CitingPaper]:
        """Find papers that cite the original publication"""
        # 1. Get original publication PMID
        original_pub = await self.get_original_publication(geo_id)
        
        # 2. Search citation databases
        citing_papers = []
        
        # Google Scholar API
        scholar_results = await self.scholar_client.get_citations(original_pub.pmid)
        citing_papers.extend(scholar_results)
        
        # Crossref API
        crossref_results = await self.crossref_client.get_citations(original_pub.doi)
        citing_papers.extend(crossref_results)
        
        # PubMed citation search
        pubmed_results = await self.pubmed_client.search_citations(original_pub.pmid)
        citing_papers.extend(pubmed_results)
        
        return self.deduplicate_and_rank(citing_papers)
    
    async def analyze_citation_context(self, citing_paper: CitingPaper) -> CitationContext:
        """Analyze how the dataset is used in citing paper"""
        full_text = await self.get_full_text(citing_paper)
        
        # Find mentions of the dataset
        dataset_mentions = self.find_dataset_mentions(full_text, citing_paper.geo_id)
        
        # Classify usage type
        usage_type = self.classify_usage_type(dataset_mentions, full_text)
        
        return CitationContext(
            paper=citing_paper,
            usage_type=usage_type,  # reanalysis, validation, meta-analysis, etc.
            mention_contexts=dataset_mentions,
            relevance_score=self.calculate_relevance_score(dataset_mentions)
        )
```

**ML/Bioinformatics Project Detection**:
```python
class MLProjectDetector:
    """Detect machine learning and bioinformatics usage"""
    
    def __init__(self):
        self.ml_keywords = [
            "machine learning", "deep learning", "neural network",
            "random forest", "support vector machine", "clustering",
            "classification", "regression", "feature selection",
            "cross-validation", "hyperparameter tuning"
        ]
        
        self.bioinformatics_keywords = [
            "differential expression", "pathway analysis", "gene ontology",
            "network analysis", "sequence alignment", "variant calling",
            "transcriptome analysis", "proteomics", "metabolomics"
        ]
    
    async def detect_ml_usage(self, paper: Paper) -> MLUsageAnalysis:
        """Detect and analyze ML usage in paper"""
        full_text = await self.get_full_text(paper)
        
        # Extract methods section
        methods_section = self.extract_methods_section(full_text)
        
        # Detect ML techniques
        ml_techniques = self.detect_techniques(methods_section, self.ml_keywords)
        
        # Extract software/tools mentioned
        software_tools = self.extract_software_mentions(methods_section)
        
        # Analyze code availability
        code_availability = await self.check_code_availability(paper)
        
        return MLUsageAnalysis(
            techniques_used=ml_techniques,
            software_tools=software_tools,
            code_available=code_availability,
            reproducibility_score=self.calculate_reproducibility_score(paper)
        )
```

### **2.3 Semantic Analysis**

**Content Similarity Engine**:
```python
class SemanticSimilarityAnalyzer:
    """Find semantically similar publications"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('allenai/scibert_scivocab_uncased')
        self.vector_store = ChromaDB()
    
    async def find_similar_publications(self, target_paper: Paper) -> List[SimilarPaper]:
        """Find semantically similar publications"""
        # Generate embeddings for target paper
        target_embedding = self.generate_paper_embedding(target_paper)
        
        # Search vector store for similar papers
        similar_papers = await self.vector_store.similarity_search(
            target_embedding,
            k=50,
            filter_criteria={"domain": "biomedical"}
        )
        
        # Re-rank based on multiple criteria
        ranked_papers = self.rerank_by_relevance(similar_papers, target_paper)
        
        return ranked_papers[:20]  # Top 20 most relevant
    
    def generate_paper_embedding(self, paper: Paper) -> np.ndarray:
        """Generate dense embeddings for paper"""
        text_components = [
            paper.title,
            paper.abstract,
            " ".join(paper.keywords),
            paper.methods_summary if hasattr(paper, 'methods_summary') else ""
        ]
        
        combined_text = " [SEP] ".join(text_components)
        embedding = self.embedding_model.encode(combined_text)
        
        return embedding
```

### **2.4 Implementation Timeline**

**Phase 1 (Weeks 1-2): Core Discovery**
- [ ] Citation tracking implementation
- [ ] Basic semantic similarity
- [ ] ML/bioinformatics keyword detection
- [ ] Database schema for relationships

**Phase 2 (Weeks 3-4): Advanced Analysis**
- [ ] Context analysis for citations
- [ ] Advanced ML technique detection
- [ ] Supplementary file analysis
- [ ] Knowledge graph construction

**Phase 3 (Weeks 5-6): Integration & Optimization**
- [ ] Real-time discovery pipeline
- [ ] Recommendation engine
- [ ] Performance optimization
- [ ] Quality metrics and validation

---

## 📈 **Module 3: Statistical Information Extraction System**

### **3.1 System Architecture**

```python
src/omics_oracle/stats_extraction/
├── __init__.py
├── text_stats_extractor.py    # Extract stats from text
├── table_processor.py         # Table data extraction
├── figure_analyzer.py         # Figure analysis and OCR
├── data_reader.py            # Direct data access
├── statistical_analyzer.py    # Compute summary statistics
├── metadata_enricher.py      # Enhance with computed stats
└── validation_engine.py      # Validate extracted statistics
```

### **3.2 Multi-Source Statistics Extraction**

**Text-Based Statistics Extraction**:
```python
class TextStatsExtractor:
    """Extract statistical information from publication text"""
    
    def __init__(self):
        self.stats_patterns = {
            'sample_size': [
                r'n\s*=\s*(\d+)',
                r'(\d+)\s+samples?',
                r'total of (\d+) subjects?'
            ],
            'p_values': [
                r'p\s*[<>=]\s*(0\.\d+)',
                r'P\s*[<>=]\s*(0\.\d+)',
                r'p-value\s*[<>=]\s*(0\.\d+)'
            ],
            'effect_sizes': [
                r'fold[- ]?change\s*[<>=]\s*([\d.]+)',
                r'log2\s*FC\s*[<>=]\s*([\d.-]+)',
                r'effect size\s*[<>=]\s*([\d.]+)'
            ]
        }
    
    async def extract_statistics_from_text(self, publication: Publication) -> TextStatistics:
        """Extract statistical measures from publication text"""
        full_text = await self.get_full_text(publication)
        
        extracted_stats = {}
        
        # Extract different types of statistics
        for stat_type, patterns in self.stats_patterns.items():
            extracted_stats[stat_type] = []
            
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                extracted_stats[stat_type].extend(matches)
        
        # Extract methodology information
        methods_info = self.extract_methods_info(full_text)
        
        # Extract sample characteristics
        sample_characteristics = self.extract_sample_characteristics(full_text)
        
        return TextStatistics(
            statistical_measures=extracted_stats,
            methodology=methods_info,
            sample_characteristics=sample_characteristics,
            confidence_scores=self.calculate_confidence_scores(extracted_stats)
        )
```

**Table Processing Engine**:
```python
class TableProcessor:
    """Extract and analyze tabular data from publications"""
    
    async def extract_tables_from_publication(self, publication: Publication) -> List[ExtractedTable]:
        """Extract all tables from publication"""
        tables = []
        
        # Extract from different sources
        if publication.pmc_id:
            pmc_tables = await self.extract_from_pmc(publication.pmc_id)
            tables.extend(pmc_tables)
        
        if publication.pdf_url:
            pdf_tables = await self.extract_from_pdf(publication.pdf_url)
            tables.extend(pdf_tables)
        
        # Process and standardize tables
        processed_tables = []
        for table in tables:
            processed_table = await self.process_table(table)
            if processed_table.statistical_content_score > 0.5:
                processed_tables.append(processed_table)
        
        return processed_tables
    
    async def process_table(self, raw_table: RawTable) -> ExtractedTable:
        """Process and analyze table content"""
        # Clean and standardize table data
        cleaned_data = self.clean_table_data(raw_table.data)
        
        # Detect column types (categorical, numerical, statistical)
        column_types = self.detect_column_types(cleaned_data)
        
        # Extract statistical relationships
        statistical_relationships = self.find_statistical_relationships(cleaned_data)
        
        # Calculate summary statistics
        summary_stats = self.calculate_summary_statistics(cleaned_data, column_types)
        
        return ExtractedTable(
            title=raw_table.title,
            caption=raw_table.caption,
            data=cleaned_data,
            column_types=column_types,
            summary_statistics=summary_stats,
            statistical_relationships=statistical_relationships,
            statistical_content_score=self.calculate_statistical_content_score(cleaned_data)
        )
```

**Direct Data Analysis**:
```python
class DirectDataAnalyzer:
    """Analyze dataset directly from NCBI GEO"""
    
    async def analyze_geo_dataset(self, geo_id: str) -> DatasetStatistics:
        """Compute comprehensive statistics from raw dataset"""
        # Download dataset metadata and sample data
        geo_data = await self.geo_client.get_dataset_with_samples(geo_id)
        
        # Basic dataset characteristics
        basic_stats = self.compute_basic_statistics(geo_data)
        
        # Sample distribution analysis
        sample_distribution = self.analyze_sample_distribution(geo_data.samples)
        
        # Platform and technology analysis
        platform_analysis = self.analyze_platform_characteristics(geo_data.platform_info)
        
        # Experimental design analysis
        experimental_design = self.analyze_experimental_design(geo_data.samples)
        
        # Quality metrics (if expression data available)
        quality_metrics = await self.compute_quality_metrics(geo_data)
        
        return DatasetStatistics(
            basic_statistics=basic_stats,
            sample_distribution=sample_distribution,
            platform_analysis=platform_analysis,
            experimental_design=experimental_design,
            quality_metrics=quality_metrics,
            computational_complexity=self.estimate_computational_complexity(geo_data)
        )
    
    def compute_basic_statistics(self, geo_data: GEODataset) -> BasicStatistics:
        """Compute basic dataset statistics"""
        return BasicStatistics(
            total_samples=len(geo_data.samples),
            total_features=geo_data.feature_count,
            organism=geo_data.organism,
            tissue_types=self.extract_tissue_types(geo_data.samples),
            cell_types=self.extract_cell_types(geo_data.samples),
            treatment_conditions=self.extract_treatment_conditions(geo_data.samples),
            time_points=self.extract_time_points(geo_data.samples),
            data_processing_pipeline=geo_data.processing_info
        )
```

### **3.3 Implementation Timeline**

**Phase 1 (Weeks 1-2): Foundation**
- [ ] Text statistics extraction
- [ ] Basic table processing
- [ ] Direct GEO data access
- [ ] Statistics validation framework

**Phase 2 (Weeks 3-4): Enhancement**
- [ ] Figure analysis and OCR
- [ ] Advanced table analysis
- [ ] Statistical relationship detection
- [ ] Quality assessment metrics

**Phase 3 (Weeks 5-6): Integration**
- [ ] Multi-source statistics aggregation
- [ ] Confidence scoring system
- [ ] API endpoints for statistics
- [ ] Caching and performance optimization

---

## 📊 **Module 4: Advanced Visualization System**

### **4.1 System Architecture**

```python
src/omics_oracle/visualization/
├── __init__.py
├── metadata_visualizer.py     # Search result visualizations
├── statistics_visualizer.py   # Statistical summaries
├── relationship_visualizer.py # Publication relationships
├── temporal_visualizer.py     # Time-based analysis
├── interactive_dashboard.py   # Interactive components
├── export_engine.py          # Export capabilities
└── chart_factory.py          # Chart generation
```

### **4.2 Visualization Components**

**Metadata Summary Visualizations**:
```python
class MetadataVisualizer:
    """Create visualizations for search result metadata"""
    
    async def create_search_overview(self, search_results: List[GEODataset]) -> SearchOverviewViz:
        """Create comprehensive search result overview"""
        visualizations = {}
        
        # Organism distribution
        visualizations['organism_distribution'] = self.create_organism_chart(search_results)
        
        # Platform technology distribution
        visualizations['platform_distribution'] = self.create_platform_chart(search_results)
        
        # Publication timeline
        visualizations['publication_timeline'] = self.create_timeline_chart(search_results)
        
        # Sample size distribution
        visualizations['sample_size_distribution'] = self.create_sample_size_chart(search_results)
        
        # Geographic distribution
        visualizations['geographic_distribution'] = self.create_geographic_chart(search_results)
        
        return SearchOverviewViz(
            charts=visualizations,
            summary_statistics=self.compute_search_summary_stats(search_results),
            interactive_filters=self.create_filter_interface(search_results)
        )
    
    def create_organism_chart(self, datasets: List[GEODataset]) -> PlotlyChart:
        """Create organism distribution chart"""
        organism_counts = Counter([d.organism for d in datasets])
        
        fig = px.pie(
            values=list(organism_counts.values()),
            names=list(organism_counts.keys()),
            title="Dataset Distribution by Organism"
        )
        
        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>" +
                         "Count: %{value}<br>" +
                         "Percentage: %{percent}<br>" +
                         "<extra></extra>"
        )
        
        return PlotlyChart(
            figure=fig,
            chart_type="pie",
            data_source="search_results",
            interactivity_level="high"
        )
```

**Statistical Summary Visualizations**:
```python
class StatisticsVisualizer:
    """Create visualizations for extracted statistics"""
    
    async def create_statistics_dashboard(self, dataset_stats: DatasetStatistics) -> StatsDashboard:
        """Create comprehensive statistics dashboard"""
        dashboard_components = {}
        
        # Sample characteristics heatmap
        dashboard_components['sample_heatmap'] = self.create_sample_heatmap(dataset_stats)
        
        # Quality metrics radar chart
        dashboard_components['quality_radar'] = self.create_quality_radar(dataset_stats)
        
        # Statistical distribution plots
        dashboard_components['distributions'] = self.create_distribution_plots(dataset_stats)
        
        # Experimental design visualization
        dashboard_components['experimental_design'] = self.create_design_visualization(dataset_stats)
        
        return StatsDashboard(
            components=dashboard_components,
            metadata=dataset_stats,
            export_options=self.get_export_options()
        )
    
    def create_sample_heatmap(self, stats: DatasetStatistics) -> PlotlyChart:
        """Create sample characteristics heatmap"""
        # Prepare data matrix for heatmap
        characteristics_matrix = self.prepare_characteristics_matrix(stats.sample_distribution)
        
        fig = px.imshow(
            characteristics_matrix,
            title="Sample Characteristics Overview",
            color_continuous_scale="Viridis"
        )
        
        fig.update_layout(
            xaxis_title="Sample Characteristics",
            yaxis_title="Sample Groups"
        )
        
        return PlotlyChart(
            figure=fig,
            chart_type="heatmap",
            data_source="dataset_statistics",
            interactivity_level="medium"
        )
```

**Interactive Dashboard Components**:
```python
class InteractiveDashboard:
    """Create interactive dashboard components"""
    
    async def create_publication_network(self, related_pubs: List[RelatedPublication]) -> NetworkViz:
        """Create interactive publication relationship network"""
        # Build network graph
        G = nx.Graph()
        
        # Add nodes (publications)
        for pub in related_pubs:
            G.add_node(pub.pmid, 
                      title=pub.title,
                      authors=pub.authors,
                      citation_count=pub.citation_count,
                      relevance_score=pub.relevance_score)
        
        # Add edges (relationships)
        for pub in related_pubs:
            for related in pub.related_publications:
                G.add_edge(pub.pmid, related.pmid, 
                          relationship_type=related.relationship_type,
                          strength=related.relationship_strength)
        
        # Create interactive visualization
        network_viz = self.create_interactive_network(G)
        
        return NetworkViz(
            graph=G,
            visualization=network_viz,
            interaction_callbacks=self.get_network_callbacks(),
            export_formats=['png', 'svg', 'html']
        )
    
    def create_temporal_analysis(self, temporal_data: TemporalData) -> TemporalViz:
        """Create temporal analysis visualizations"""
        components = {}
        
        # Publication timeline
        components['publication_timeline'] = self.create_publication_timeline(temporal_data)
        
        # Citation trends
        components['citation_trends'] = self.create_citation_trends(temporal_data)
        
        # Technology evolution
        components['technology_evolution'] = self.create_technology_evolution(temporal_data)
        
        return TemporalViz(
            components=components,
            time_range=temporal_data.time_range,
            animation_controls=True
        )
```

### **4.3 Implementation Timeline**

**Phase 1 (Weeks 1-2): Core Visualizations**
- [ ] Basic metadata charts
- [ ] Statistical summary plots
- [ ] Chart export functionality
- [ ] Responsive design implementation

**Phase 2 (Weeks 3-4): Interactive Features**
- [ ] Interactive filtering and drilling
- [ ] Publication network visualization
- [ ] Temporal analysis components
- [ ] Real-time data updates

**Phase 3 (Weeks 5-6): Advanced Features**
- [ ] Custom dashboard builder
- [ ] Advanced export options
- [ ] Performance optimization
- [ ] Mobile-responsive design

---

## 🔄 **Interface Architecture Review & Updates**

### **5.1 Impact Assessment on Existing Interface Plans**

Based on these advanced modules, our interface consolidation strategy needs several updates:

**Required Interface Enhancements**:

1. **Real-Time Data Streaming**: WebSocket support for live visualization updates
2. **Advanced Frontend Components**: Rich visualization library integration
3. **Enhanced API Endpoints**: Support for complex data queries and streaming
4. **Background Processing**: Queue system for text extraction and analysis
5. **Storage Architecture**: Extended database schema for extracted content

### **5.2 Updated Interface Architecture**

**Enhanced FastAPI Web Interface**:
```python
# Updated web interface structure
src/omics_oracle/web/
├── main.py                    # Enhanced FastAPI app
├── models.py                  # Extended data models
├── visualization/             # NEW: Visualization components
│   ├── charts.py
│   ├── dashboards.py
│   └── interactive.py
├── streaming/                 # NEW: Real-time data streaming
│   ├── websockets.py
│   └── sse.py
├── background_tasks/          # NEW: Async processing
│   ├── text_extraction.py
│   └── statistics_computation.py
└── templates/                 # Enhanced templates
    ├── dashboard.html         # Enhanced with new visualizations
    ├── publication_network.html # NEW
    └── statistics_viewer.html   # NEW
```

**Enhanced API Endpoints**:
```python
# New API endpoints for advanced features
@app.get("/api/v1/publications/{geo_id}/full-text")
async def get_full_text(geo_id: str) -> FullTextResponse:
    """Get extracted full text for dataset publication"""
    pass

@app.get("/api/v1/publications/{geo_id}/related")
async def get_related_publications(geo_id: str) -> RelatedPublicationsResponse:
    """Get publications that used this dataset"""
    pass

@app.get("/api/v1/datasets/{geo_id}/statistics")
async def get_dataset_statistics(geo_id: str) -> DatasetStatisticsResponse:
    """Get comprehensive dataset statistics"""
    pass

@app.get("/api/v1/visualizations/{viz_type}")
async def get_visualization_data(viz_type: str, **params) -> VisualizationResponse:
    """Get data for specific visualization types"""
    pass

@app.websocket("/ws/dataset/{geo_id}/live-stats")
async def dataset_live_stats(websocket: WebSocket, geo_id: str):
    """Stream live statistics updates"""
    pass
```

### **5.3 Frontend Technology Stack Updates**

**Enhanced React Components**:
```typescript
// New React components for advanced features
src/components/
├── visualizations/
│   ├── MetadataCharts.tsx
│   ├── StatisticsDashboard.tsx
│   ├── PublicationNetwork.tsx
│   └── TemporalAnalysis.tsx
├── text-extraction/
│   ├── FullTextViewer.tsx
│   ├── StatisticsExtractor.tsx
│   └── QualityIndicator.tsx
└── real-time/
    ├── LiveDataStream.tsx
    ├── ProcessingStatus.tsx
    └── NotificationCenter.tsx
```

**Required Library Additions**:
```json
{
  "dependencies": {
    "plotly.js": "^2.26.0",
    "react-plotly.js": "^2.6.0",
    "d3": "^7.8.5",
    "vis-network": "^9.1.6",
    "socket.io-client": "^4.7.2",
    "react-virtualized": "^9.22.5",
    "pdf-viewer-react": "^2.2.3"
  }
}
```

### **5.4 Updated Implementation Priority**

**Revised Interface Consolidation Timeline**:

**Phase 1 (Weeks 1-2): Foundation + Preparation**
- [ ] Complete basic interface consolidation
- [ ] Add WebSocket infrastructure
- [ ] Implement basic visualization framework
- [ ] Set up background task system

**Phase 2 (Weeks 3-4): Core Feature Integration**
- [ ] Integrate text extraction APIs
- [ ] Add basic statistics visualization
- [ ] Implement publication discovery endpoints
- [ ] Create responsive dashboard layout

**Phase 3 (Weeks 5-8): Advanced Features**
- [ ] Full-text extraction system
- [ ] Related publications discovery
- [ ] Advanced statistical analysis
- [ ] Interactive visualization dashboard

**Phase 4 (Weeks 9-12): Optimization & Polish**
- [ ] Performance optimization
- [ ] Mobile responsiveness
- [ ] Advanced export capabilities
- [ ] User experience refinement

---

## 📊 **Resource Requirements Update**

### **6.1 Technical Infrastructure**

**Additional Storage Requirements**:
- Full-text content storage: ~100GB for 10K publications
- Extracted statistics cache: ~10GB
- Visualization data cache: ~5GB
- Processing logs and metadata: ~2GB

**Processing Power Requirements**:
- PDF text extraction: CPU-intensive (8+ cores recommended)
- NLP processing: GPU acceleration beneficial
- Large dataset analysis: Memory-intensive (32GB+ RAM)
- Real-time visualizations: Fast I/O and caching

**External API Dependencies**:
- PubMed Central API access
- DOI resolution services
- PDF processing services
- Citation database APIs

### **6.2 Development Resources**

**Skill Requirements**:
- NLP and text processing expertise
- Advanced data visualization (D3.js, Plotly)
- Scientific publication analysis knowledge
- Performance optimization experience
- Real-time web application development

**Estimated Development Time**:
- Text extraction system: 6-8 weeks
- Publication discovery: 4-6 weeks  
- Statistics extraction: 6-8 weeks
- Visualization dashboard: 4-6 weeks
- Integration and testing: 4-6 weeks

**Total Estimated Timeline**: 24-34 weeks (6-8 months) for complete implementation

---

## 🎯 **Success Metrics & KPIs**

### **6.3 Module-Specific Success Criteria**

**Text Extraction Module**:
- [ ] 95%+ success rate for PMC full-text extraction
- [ ] 80%+ success rate for PDF text extraction
- [ ] <30 seconds average processing time per publication
- [ ] 90%+ text quality score for extracted content

**Publication Discovery Module**:
- [ ] Identify 80%+ of relevant citing publications
- [ ] 70%+ accuracy in ML/bioinformatics classification
- [ ] <5 seconds response time for related publication queries
- [ ] 85%+ user satisfaction with recommendation quality

**Statistics Extraction Module**:
- [ ] Extract statistics from 90%+ of publications with tabular data
- [ ] 80%+ accuracy in statistical value extraction
- [ ] Comprehensive metadata for 95%+ of GEO datasets
- [ ] Real-time statistics computation for datasets <10K samples

**Visualization Module**:
- [ ] <2 seconds load time for standard visualizations
- [ ] Support for 20+ different chart types
- [ ] Mobile-responsive design across all visualizations
- [ ] 95%+ user satisfaction with dashboard usability

---

## 📝 **Conclusion & Next Steps**

These four advanced modules will transform OmicsOracle from a basic search tool into a comprehensive biomedical research intelligence platform. The integration of full-text analysis, publication tracking, statistical extraction, and advanced visualization will provide researchers with unprecedented insights into biomedical datasets and their usage across the scientific community.

**Key Strategic Advantages**:

1. **Comprehensive Content Analysis**: Full-text extraction provides deep insights beyond metadata
2. **Research Impact Tracking**: Understanding how datasets are used in subsequent research
3. **Data-Driven Insights**: Statistical summaries enable quick dataset assessment
4. **Visual Intelligence**: Advanced visualizations reveal patterns and relationships

**Recommended Implementation Approach**:

1. **Start with Interface Foundation**: Complete the interface consolidation with these advanced features in mind
2. **Prototype Core Modules**: Build MVPs of each module to validate technical feasibility
3. **Iterative Integration**: Integrate modules one by one with thorough testing
4. **User Feedback Loop**: Continuously gather feedback and refine features

The updated interface architecture now properly supports these advanced capabilities while maintaining the clean, consolidated structure identified in our original analysis. This approach ensures that OmicsOracle will be well-positioned to become the leading platform for intelligent biomedical data discovery and analysis.
