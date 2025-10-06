# 🔄 Refactored Integration Strategy

**Status:** Architecture-Aligned Enhancement Plan  
**Date:** January 2025  
**Purpose:** Refactor enhancement plans to leverage existing modular architecture

---

## 📋 Executive Summary

**CRITICAL CHANGES FROM ORIGINAL PLANS:**

❌ **Original Approach:**
- 7 new top-level lib/ modules
- SearchAgent directly manages 10+ components
- Flat orchestration without feature toggles
- Complex integration

✅ **Refactored Approach:**
- 3 consolidated lib/ modules
- SearchAgent manages 3-4 pipelines
- Feature toggles for incremental adoption
- Follows existing AdvancedSearchPipeline pattern

**KEY INSIGHT:** The existing `AdvancedSearchPipeline` pattern is **EXACTLY** what we need. All enhancements should follow this golden pattern.

---

## 🎯 Refactored Module Organization

### **From 7 Modules → 3 Consolidated Modules**

#### **Module 1: lib/publications/** (Publication Mining)
**Consolidates:** Original `publications/`, `pdf/`, `web/` modules

```
lib/publications/
├── __init__.py
├── pipeline.py                    # PublicationSearchPipeline (golden pattern)
├── config.py                      # PublicationSearchConfig
├── models.py                      # Publication, FullText, Citation models
│
├── clients/                       # API clients
│   ├── __init__.py
│   ├── pubmed.py                 # PubMed/NCBI client
│   ├── pmc.py                    # PMC full-text client
│   ├── europe_pmc.py             # Europe PMC client
│   ├── scholar.py                # Google Scholar scraping
│   └── base.py                   # Base publication client
│
├── pdf/                          # PDF processing
│   ├── __init__.py
│   ├── downloader.py             # Multi-source PDF download
│   ├── scraper.py                # Web PDF scraping
│   ├── grobid.py                 # GROBID text extraction
│   └── parser.py                 # PDF parsing utilities
│
└── analysis/                     # Publication analysis
    ├── __init__.py
    ├── citation.py               # Citation analysis
    ├── trends.py                 # Trending topics detection
    └── knowledge.py              # Knowledge enrichment
```

**Rationale:**
- ✅ All publication-related functionality in one place
- ✅ Clear sub-organization (clients/, pdf/, analysis/)
- ✅ Easy to understand and navigate
- ✅ Follows existing lib/ module pattern

#### **Module 2: lib/llm/** (LLM Enhancements)
**Consolidates:** Original `query/`, `llm/` modules + LLM features

```
lib/llm/
├── __init__.py
├── pipeline.py                    # LLMEnhancedSearchPipeline (golden pattern)
├── config.py                      # LLMConfig with model assignments
├── models.py                      # LLM input/output models
│
├── query/                         # Query enhancement
│   ├── __init__.py
│   ├── reformulator.py           # BiomedicalQueryReformulator (BioMistral-7B)
│   ├── expander.py               # Multi-aspect query expansion
│   └── validator.py              # Query validation
│
├── embeddings/                    # Advanced embeddings
│   ├── __init__.py
│   ├── biomedical.py             # AdvancedBiomedicalEmbeddings (E5-Mistral-7B)
│   ├── hybrid.py                 # Hybrid embedding strategies
│   └── cache.py                  # Embedding cache
│
├── ranking/                       # LLM reranking
│   ├── __init__.py
│   ├── reranker.py               # LLMReranker (Llama-3.1-8B)
│   └── explainer.py              # Explainability features
│
└── synthesis/                     # Advanced synthesis
    ├── __init__.py
    ├── multi_paper.py            # MultiPaperSynthesizer (Meditron-70B)
    ├── hypothesis.py             # HypothesisGenerator (Falcon-180B)
    └── summarizer.py             # Summary generation
```

**Rationale:**
- ✅ All LLM functionality in one module
- ✅ Organized by LLM use case (query/, embeddings/, ranking/, synthesis/)
- ✅ Easy GPU allocation (module = GPU assignment)
- ✅ Clear model ownership

#### **Module 3: lib/integration/** (Multi-Source Integration)
**Consolidates:** Original `integration/`, `knowledge/` modules

```
lib/integration/
├── __init__.py
├── pipeline.py                    # IntegrationPipeline (golden pattern)
├── config.py                      # IntegrationConfig
├── models.py                      # Integrated result models
│
├── fusion/                        # Cross-source fusion
│   ├── __init__.py
│   ├── ranker.py                 # UnifiedRanker (datasets + publications)
│   ├── deduplicator.py           # Cross-source deduplication
│   └── scorer.py                 # Unified relevance scoring
│
└── knowledge/                     # Knowledge extraction
    ├── __init__.py
    ├── entities.py               # Entity extraction & linking
    ├── relationships.py          # Relationship extraction
    └── graph.py                  # Knowledge graph construction
```

**Rationale:**
- ✅ Integration logic separate from data sources
- ✅ Knowledge graph capabilities included
- ✅ Clear fusion strategy

---

## 🏗️ Pipeline Architecture (Following Golden Pattern)

### **Golden Pattern: AdvancedSearchPipeline**

**Every new pipeline follows this exact structure:**

```python
# 1. Configuration with feature toggles
@dataclass
class XYZConfig:
    enable_feature_1: bool = True
    enable_feature_2: bool = False
    feature_1_config: Optional[Feature1Config] = None
    feature_2_config: Optional[Feature2Config] = None

# 2. Pipeline with conditional initialization
class XYZPipeline:
    def __init__(self, config: XYZConfig):
        # Conditional initialization
        if config.enable_feature_1:
            self.feature_1 = Feature1(config.feature_1_config)
        else:
            self.feature_1 = None
        
        # Core components (always initialized)
        self.core_component = CoreComponent(config.core_config)
    
    # 3. Clean execution with conditional features
    def execute(self, input_data) -> OutputData:
        # Use features conditionally
        if self.feature_1:
            result = self.feature_1.process(input_data)
        else:
            result = input_data
        
        return OutputData(...)
```

### **Pipeline 1: PublicationSearchPipeline**

**Follows golden pattern:**

```python
from dataclasses import dataclass, field
from typing import Optional, List
from .clients import PubMedClient, GoogleScholarClient
from .pdf import PDFDownloader, FullTextExtractor
from .analysis import CitationAnalyzer
from .models import PublicationResult, Publication

@dataclass
class PubMedConfig:
    api_key: Optional[str] = None
    max_results: int = 50
    email: Optional[str] = None

@dataclass
class ScholarConfig:
    use_selenium: bool = True
    max_results: int = 20
    rate_limit_delay: float = 2.0

@dataclass
class PDFConfig:
    download_timeout: int = 30
    max_file_size_mb: int = 50
    grobid_url: str = "http://localhost:8070"

@dataclass
class PublicationSearchConfig:
    """Configuration for publication search pipeline"""
    
    # Feature toggles
    enable_pubmed: bool = True
    enable_scholar: bool = False
    enable_pmc: bool = False
    enable_citations: bool = False
    enable_pdf_download: bool = False
    enable_fulltext: bool = False
    
    # Component configs
    pubmed_config: PubMedConfig = field(default_factory=PubMedConfig)
    scholar_config: ScholarConfig = field(default_factory=ScholarConfig)
    pdf_config: PDFConfig = field(default_factory=PDFConfig)


class PublicationSearchPipeline:
    """
    Publication search pipeline following AdvancedSearchPipeline pattern.
    
    Features (toggle via config):
    - PubMed search (enable_pubmed)
    - Google Scholar search (enable_scholar)
    - PMC full-text (enable_pmc)
    - Citation analysis (enable_citations)
    - PDF download (enable_pdf_download)
    - Full-text extraction (enable_fulltext)
    """
    
    def __init__(self, config: PublicationSearchConfig):
        self.config = config
        
        # Conditional initialization based on feature toggles
        if config.enable_pubmed:
            self.pubmed_client = PubMedClient(config.pubmed_config)
        else:
            self.pubmed_client = None
        
        if config.enable_scholar:
            self.scholar_client = GoogleScholarClient(config.scholar_config)
        else:
            self.scholar_client = None
        
        if config.enable_citations:
            self.citation_analyzer = CitationAnalyzer()
        else:
            self.citation_analyzer = None
        
        if config.enable_pdf_download:
            self.pdf_downloader = PDFDownloader(config.pdf_config)
        else:
            self.pdf_downloader = None
        
        if config.enable_fulltext:
            self.fulltext_extractor = FullTextExtractor(config.pdf_config)
        else:
            self.fulltext_extractor = None
        
        # Core component (always initialized)
        self.publication_ranker = PublicationRanker()
    
    def search(
        self,
        query: str,
        max_results: int = 50,
        filters: Optional[dict] = None
    ) -> PublicationResult:
        """
        Execute publication search with conditional features.
        
        Args:
            query: Search query
            max_results: Maximum results per source
            filters: Optional filters (year, journal, etc.)
        
        Returns:
            PublicationResult with publications
        """
        publications = []
        
        # Step 1: Search PubMed (if enabled)
        if self.pubmed_client:
            pubmed_results = self.pubmed_client.search(
                query, 
                max_results=max_results,
                filters=filters
            )
            publications.extend(pubmed_results)
        
        # Step 2: Search Google Scholar (if enabled)
        if self.scholar_client:
            scholar_results = self.scholar_client.search(
                query,
                max_results=max_results
            )
            publications.extend(scholar_results)
        
        # Step 3: Rank and deduplicate (always executed)
        publications = self.publication_ranker.rank(publications, query)
        
        # Step 4: Analyze citations (if enabled)
        if self.citation_analyzer:
            publications = self.citation_analyzer.analyze(publications)
        
        # Step 5: Download PDFs (if enabled)
        if self.pdf_downloader:
            publications = self.pdf_downloader.download(publications)
        
        # Step 6: Extract full text (if enabled)
        if self.fulltext_extractor:
            publications = self.fulltext_extractor.extract(publications)
        
        return PublicationResult(
            query=query,
            publications=publications,
            total_found=len(publications),
            sources_used=self._get_sources_used(),
            features_enabled=self._get_enabled_features()
        )
    
    def _get_sources_used(self) -> List[str]:
        """Get list of enabled sources"""
        sources = []
        if self.pubmed_client:
            sources.append("pubmed")
        if self.scholar_client:
            sources.append("scholar")
        return sources
    
    def _get_enabled_features(self) -> List[str]:
        """Get list of enabled features"""
        features = []
        if self.citation_analyzer:
            features.append("citations")
        if self.pdf_downloader:
            features.append("pdf_download")
        if self.fulltext_extractor:
            features.append("fulltext")
        return features
```

**Key Points:**
- ✅ Follows AdvancedSearchPipeline pattern EXACTLY
- ✅ Feature toggles for every capability
- ✅ Conditional initialization (no overhead for disabled features)
- ✅ Clean, linear execution flow
- ✅ Easy to test (enable/disable features)
- ✅ Incremental adoption (start with PubMed, add Scholar later)

### **Pipeline 2: LLMEnhancedSearchPipeline**

**Follows golden pattern:**

```python
from dataclasses import dataclass, field
from typing import Optional
from .query import BiomedicalQueryReformulator
from .embeddings import AdvancedBiomedicalEmbeddings
from .ranking import LLMReranker
from .synthesis import MultiPaperSynthesizer, HypothesisGenerator
from ..search.advanced import AdvancedSearchPipeline

@dataclass
class LLMModelConfig:
    """LLM model configuration"""
    model_name: str
    gpu_id: int
    quantization: Optional[str] = None  # 8bit, 4bit
    max_length: int = 4096
    temperature: float = 0.1

@dataclass
class LLMEnhancedConfig:
    """Configuration for LLM-enhanced search pipeline"""
    
    # Feature toggles
    enable_llm_reformulation: bool = False
    enable_llm_embeddings: bool = False
    enable_llm_reranking: bool = False
    enable_synthesis: bool = False
    enable_hypotheses: bool = False
    
    # LLM model configs
    reformulation_model: LLMModelConfig = field(
        default_factory=lambda: LLMModelConfig(
            model_name="BioMistral-7B",
            gpu_id=0,
            quantization="8bit"
        )
    )
    embedding_model: LLMModelConfig = field(
        default_factory=lambda: LLMModelConfig(
            model_name="intfloat/e5-mistral-7b-instruct",
            gpu_id=0,
            max_length=32768
        )
    )
    reranking_model: LLMModelConfig = field(
        default_factory=lambda: LLMModelConfig(
            model_name="meta-llama/Llama-3.1-8B-Instruct",
            gpu_id=1
        )
    )
    synthesis_model: LLMModelConfig = field(
        default_factory=lambda: LLMModelConfig(
            model_name="epfl-llm/meditron-70b",
            gpu_id=2  # Will use 2 GPUs
        )
    )
    
    # Base pipeline config (for non-LLM search)
    base_pipeline_config: Optional[AdvancedSearchConfig] = None


class LLMEnhancedSearchPipeline:
    """
    LLM-enhanced search pipeline following AdvancedSearchPipeline pattern.
    
    LLM Features (toggle via config):
    - Query reformulation (BioMistral-7B) - enable_llm_reformulation
    - Advanced embeddings (E5-Mistral-7B) - enable_llm_embeddings
    - Explainable reranking (Llama-3.1-8B) - enable_llm_reranking
    - Multi-paper synthesis (Meditron-70B) - enable_synthesis
    - Hypothesis generation (Falcon-180B) - enable_hypotheses
    """
    
    def __init__(self, config: LLMEnhancedConfig):
        self.config = config
        
        # Conditional LLM component initialization
        if config.enable_llm_reformulation:
            self.query_reformulator = BiomedicalQueryReformulator(
                config.reformulation_model
            )
        else:
            self.query_reformulator = None
        
        if config.enable_llm_embeddings:
            self.llm_embedder = AdvancedBiomedicalEmbeddings(
                config.embedding_model
            )
        else:
            self.llm_embedder = None
        
        if config.enable_llm_reranking:
            self.llm_reranker = LLMReranker(config.reranking_model)
        else:
            self.llm_reranker = None
        
        if config.enable_synthesis:
            self.synthesizer = MultiPaperSynthesizer(
                config.synthesis_model
            )
        else:
            self.synthesizer = None
        
        if config.enable_hypotheses:
            self.hypothesis_generator = HypothesisGenerator(
                config.synthesis_model  # Uses same model as synthesis
            )
        else:
            self.hypothesis_generator = None
        
        # Base pipeline (always initialized, may use LLM embeddings)
        base_config = config.base_pipeline_config or AdvancedSearchConfig()
        
        # If LLM embeddings enabled, override base pipeline embedding service
        if self.llm_embedder:
            base_config.embedding_config.service = self.llm_embedder
        
        self.base_pipeline = AdvancedSearchPipeline(base_config)
    
    def search(
        self,
        query: str,
        generate_hypotheses: bool = False,
        **kwargs
    ) -> EnhancedSearchResult:
        """
        Execute LLM-enhanced search with conditional features.
        
        Args:
            query: Original user query
            generate_hypotheses: Whether to generate hypotheses
            **kwargs: Additional arguments for base pipeline
        
        Returns:
            EnhancedSearchResult with LLM-powered enhancements
        """
        # Step 1: Query reformulation (if enabled)
        if self.query_reformulator:
            reformed_query, multi_aspect_queries = self.query_reformulator.reformulate(query)
        else:
            reformed_query = query
            multi_aspect_queries = [query]
        
        # Step 2: Base search (always executed, may use LLM embeddings)
        base_results = self.base_pipeline.search(reformed_query, **kwargs)
        
        # Step 3: LLM reranking (if enabled)
        if self.llm_reranker:
            reranked_results, explanations = self.llm_reranker.rerank_with_explanation(
                query, 
                base_results
            )
        else:
            reranked_results = base_results
            explanations = None
        
        # Step 4: Multi-paper synthesis (if enabled)
        synthesis = None
        if self.synthesizer:
            synthesis = self.synthesizer.synthesize_papers(
                query,
                reranked_results.top_k(10)
            )
        
        # Step 5: Hypothesis generation (if enabled and requested)
        hypotheses = None
        if self.hypothesis_generator and generate_hypotheses:
            hypotheses = self.hypothesis_generator.generate_hypotheses(
                query,
                reranked_results.top_k(5),
                synthesis
            )
        
        return EnhancedSearchResult(
            query=query,
            reformed_query=reformed_query,
            multi_aspect_queries=multi_aspect_queries,
            results=reranked_results,
            explanations=explanations,
            synthesis=synthesis,
            hypotheses=hypotheses,
            llm_features_used=self._get_llm_features_used()
        )
    
    def _get_llm_features_used(self) -> List[str]:
        """Get list of enabled LLM features"""
        features = []
        if self.query_reformulator:
            features.append("reformulation")
        if self.llm_embedder:
            features.append("llm_embeddings")
        if self.llm_reranker:
            features.append("llm_reranking")
        if self.synthesizer:
            features.append("synthesis")
        if self.hypothesis_generator:
            features.append("hypotheses")
        return features
```

**Key Points:**
- ✅ Extends AdvancedSearchPipeline, doesn't replace it
- ✅ LLM embeddings can replace standard embeddings OR run alongside
- ✅ Each LLM feature is optional (feature toggles)
- ✅ GPU assignments in config
- ✅ Clean separation of LLM logic

### **Pipeline 3: IntegrationPipeline**

**Follows golden pattern:**

```python
from dataclasses import dataclass, field
from typing import List, Optional
from .fusion import UnifiedRanker, CrossSourceDeduplicator
from .knowledge import EntityExtractor, RelationshipExtractor, KnowledgeGraph
from ..search.advanced import SearchResult
from ..publications.pipeline import PublicationResult

@dataclass
class IntegrationConfig:
    """Configuration for integration pipeline"""
    
    # Feature toggles
    enable_cross_reference: bool = True
    enable_unified_ranking: bool = True
    enable_deduplication: bool = True
    enable_entity_extraction: bool = False
    enable_knowledge_graph: bool = False
    
    # Component configs
    fusion_config: Optional[dict] = None
    knowledge_config: Optional[dict] = None


class IntegrationPipeline:
    """
    Multi-source integration pipeline following AdvancedSearchPipeline pattern.
    
    Features (toggle via config):
    - Cross-reference datasets & publications (enable_cross_reference)
    - Unified ranking (enable_unified_ranking)
    - Deduplication (enable_deduplication)
    - Entity extraction (enable_entity_extraction)
    - Knowledge graph (enable_knowledge_graph)
    """
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        
        # Conditional initialization
        if config.enable_unified_ranking:
            self.unified_ranker = UnifiedRanker()
        else:
            self.unified_ranker = None
        
        if config.enable_deduplication:
            self.deduplicator = CrossSourceDeduplicator()
        else:
            self.deduplicator = None
        
        if config.enable_entity_extraction:
            self.entity_extractor = EntityExtractor()
            self.relationship_extractor = RelationshipExtractor()
        else:
            self.entity_extractor = None
            self.relationship_extractor = None
        
        if config.enable_knowledge_graph:
            self.knowledge_graph = KnowledgeGraph()
        else:
            self.knowledge_graph = None
    
    def integrate(
        self,
        dataset_results: SearchResult,
        publication_results: PublicationResult,
        query: str
    ) -> IntegratedResult:
        """
        Integrate dataset and publication results.
        
        Args:
            dataset_results: Results from SearchAgent
            publication_results: Results from PublicationSearchPipeline
            query: Original query
        
        Returns:
            IntegratedResult with unified ranking and cross-references
        """
        # Step 1: Deduplication (if enabled)
        if self.deduplicator:
            dataset_results, publication_results = self.deduplicator.deduplicate(
                dataset_results,
                publication_results
            )
        
        # Step 2: Cross-reference (always executed)
        cross_refs = self._create_cross_references(
            dataset_results,
            publication_results
        )
        
        # Step 3: Unified ranking (if enabled)
        if self.unified_ranker:
            unified_results = self.unified_ranker.rank(
                dataset_results,
                publication_results,
                query
            )
        else:
            # Simple combination without reranking
            unified_results = self._combine_results(
                dataset_results,
                publication_results
            )
        
        # Step 4: Entity extraction (if enabled)
        entities = None
        relationships = None
        if self.entity_extractor:
            entities = self.entity_extractor.extract(unified_results)
            relationships = self.relationship_extractor.extract(
                entities,
                unified_results
            )
        
        # Step 5: Knowledge graph (if enabled)
        kg = None
        if self.knowledge_graph and entities:
            kg = self.knowledge_graph.build(entities, relationships)
        
        return IntegratedResult(
            query=query,
            unified_results=unified_results,
            cross_references=cross_refs,
            entities=entities,
            relationships=relationships,
            knowledge_graph=kg
        )
```

---

## 🔄 Updated SearchAgent Integration

### **SearchAgent with Pipeline Composition**

**Key Change:** Manage pipelines, not individual components

```python
from typing import Optional
from dataclasses import dataclass

from ..core.config import Settings
from .base import Agent
from .models.search import SearchInput, SearchOutput
from ..lib.geo import GEOClient
from ..lib.ranking import KeywordRanker
from ..lib.search.advanced import AdvancedSearchPipeline
from ..lib.publications.pipeline import PublicationSearchPipeline
from ..lib.llm.pipeline import LLMEnhancedSearchPipeline
from ..lib.integration.pipeline import IntegrationPipeline

@dataclass
class SearchAgentConfig:
    """Configuration for SearchAgent with pipeline toggles"""
    
    # Pipeline toggles
    enable_semantic: bool = False           # Existing
    enable_publications: bool = False       # NEW
    enable_llm: bool = False                # NEW
    enable_integration: bool = False        # NEW
    
    # Pipeline configs (passed through)
    search_config: Optional[AdvancedSearchConfig] = None
    publications_config: Optional[PublicationSearchConfig] = None
    llm_config: Optional[LLMEnhancedConfig] = None
    integration_config: Optional[IntegrationConfig] = None


class SearchAgent(Agent[SearchInput, SearchOutput]):
    """
    Main search agent with optional pipeline composition.
    
    Manages:
    - Core search (GEOClient + KeywordRanker)
    - Semantic search (AdvancedSearchPipeline) - optional
    - Publication search (PublicationSearchPipeline) - optional
    - LLM enhancements (LLMEnhancedSearchPipeline) - optional
    - Integration (IntegrationPipeline) - optional
    """
    
    def __init__(
        self,
        settings: Settings,
        agent_config: Optional[SearchAgentConfig] = None
    ):
        super().__init__(settings, agent_name="SearchAgent")
        self.agent_config = agent_config or SearchAgentConfig()
    
    def _initialize_resources(self) -> None:
        """Initialize resources based on enabled pipelines"""
        
        # Core components (always initialized)
        self.geo_client = GEOClient(self.settings.geo)
        self.keyword_ranker = KeywordRanker(self.settings.ranking)
        
        # Optional pipeline 1: Semantic search
        if self.agent_config.enable_semantic:
            config = self.agent_config.search_config or AdvancedSearchConfig()
            self.semantic_pipeline = AdvancedSearchPipeline(config)
        else:
            self.semantic_pipeline = None
        
        # Optional pipeline 2: Publications
        if self.agent_config.enable_publications:
            config = self.agent_config.publications_config or PublicationSearchConfig()
            self.publication_pipeline = PublicationSearchPipeline(config)
        else:
            self.publication_pipeline = None
        
        # Optional pipeline 3: LLM enhancements
        if self.agent_config.enable_llm:
            config = self.agent_config.llm_config or LLMEnhancedConfig()
            self.llm_pipeline = LLMEnhancedSearchPipeline(config)
        else:
            self.llm_pipeline = None
        
        # Optional pipeline 4: Integration
        if self.agent_config.enable_integration:
            config = self.agent_config.integration_config or IntegrationConfig()
            self.integration_pipeline = IntegrationPipeline(config)
        else:
            self.integration_pipeline = None
    
    def _cleanup_resources(self) -> None:
        """Clean up pipeline resources"""
        # Cleanup handled automatically by pipelines
        pass
    
    def _validate_input(self, input_data: SearchInput) -> SearchInput:
        """Validate search input"""
        if not input_data.search_terms:
            raise AgentValidationError("search_terms required")
        return input_data
    
    def _process(
        self,
        input_data: SearchInput,
        context: AgentContext
    ) -> SearchOutput:
        """
        Execute search with enabled pipelines.
        
        Flow:
        1. Choose search strategy (LLM > semantic > basic)
        2. Optionally search publications
        3. Optionally integrate results
        """
        # Step 1: Choose dataset search strategy
        if self.llm_pipeline:
            # LLM-enhanced search (includes semantic search)
            dataset_results = self._llm_search(input_data, context)
        elif self.semantic_pipeline:
            # Semantic search
            dataset_results = self._semantic_search(input_data, context)
        else:
            # Basic search
            dataset_results = self._basic_search(input_data, context)
        
        # Step 2: Publication search (if enabled)
        publication_results = None
        if self.publication_pipeline:
            publication_results = self._publication_search(input_data, context)
        
        # Step 3: Integration (if enabled and we have both results)
        if self.integration_pipeline and publication_results:
            integrated = self.integration_pipeline.integrate(
                dataset_results,
                publication_results,
                input_data.original_query or " ".join(input_data.search_terms)
            )
            # Convert integrated results back to SearchOutput
            # (simplified for this example)
            return SearchOutput(
                datasets=integrated.unified_results.datasets,
                total_found=len(integrated.unified_results.datasets),
                search_terms_used=input_data.search_terms,
                filters_applied={}
            )
        
        # Return dataset results
        return dataset_results
    
    def _basic_search(
        self,
        input_data: SearchInput,
        context: AgentContext
    ) -> SearchOutput:
        """Basic search with GEOClient + KeywordRanker"""
        # Search GEO
        datasets = self.geo_client.search(
            terms=input_data.search_terms,
            max_results=input_data.max_results,
            organism=input_data.organism,
            study_type=input_data.study_type
        )
        
        # Rank by keywords
        ranked = self.keyword_ranker.rank(
            datasets,
            input_data.search_terms
        )
        
        # Apply filters
        if input_data.min_samples:
            ranked = [d for d in ranked if d.dataset.sample_count >= input_data.min_samples]
        
        return SearchOutput(
            datasets=ranked,
            total_found=len(ranked),
            search_terms_used=input_data.search_terms,
            filters_applied=self._get_filters(input_data)
        )
    
    def _semantic_search(
        self,
        input_data: SearchInput,
        context: AgentContext
    ) -> SearchOutput:
        """Semantic search with AdvancedSearchPipeline"""
        query = input_data.original_query or " ".join(input_data.search_terms)
        
        results = self.semantic_pipeline.search(
            query=query,
            max_results=input_data.max_results,
            filters={
                "organism": input_data.organism,
                "study_type": input_data.study_type,
                "min_samples": input_data.min_samples
            }
        )
        
        # Convert to SearchOutput
        return SearchOutput(
            datasets=results.datasets,
            total_found=len(results.datasets),
            search_terms_used=[query],
            filters_applied=self._get_filters(input_data)
        )
    
    def _llm_search(
        self,
        input_data: SearchInput,
        context: AgentContext
    ) -> SearchOutput:
        """LLM-enhanced search with LLMEnhancedSearchPipeline"""
        query = input_data.original_query or " ".join(input_data.search_terms)
        
        results = self.llm_pipeline.search(
            query=query,
            max_results=input_data.max_results,
            filters={
                "organism": input_data.organism,
                "study_type": input_data.study_type,
                "min_samples": input_data.min_samples
            }
        )
        
        # Convert to SearchOutput
        return SearchOutput(
            datasets=results.results.datasets,
            total_found=len(results.results.datasets),
            search_terms_used=[results.reformed_query],
            filters_applied=self._get_filters(input_data)
        )
    
    def _publication_search(
        self,
        input_data: SearchInput,
        context: AgentContext
    ) -> PublicationResult:
        """Search publications with PublicationSearchPipeline"""
        query = input_data.original_query or " ".join(input_data.search_terms)
        
        return self.publication_pipeline.search(
            query=query,
            max_results=input_data.max_results
        )
    
    def _get_filters(self, input_data: SearchInput) -> dict:
        """Extract applied filters"""
        filters = {}
        if input_data.organism:
            filters["organism"] = input_data.organism
        if input_data.study_type:
            filters["study_type"] = input_data.study_type
        if input_data.min_samples:
            filters["min_samples"] = str(input_data.min_samples)
        return filters
```

**Key Benefits:**
- ✅ **Manages 4 pipelines (not 10+ components)**
- ✅ **Each pipeline is self-contained**
- ✅ **Feature toggles at agent level**
- ✅ **Clean orchestration logic**
- ✅ **Easy to test each pipeline independently**
- ✅ **Incremental adoption (enable pipelines one by one)**

---

## 📊 Feature Toggle Strategy

### **Configuration Hierarchy**

```yaml
# config/search_enhanced.yml

search_agent:
  # Pipeline toggles
  enable_semantic: true
  enable_publications: true
  enable_llm: false        # Start with False, enable when ready
  enable_integration: true
  
  # Pipeline configurations
  search_config:
    enable_query_expansion: true
    enable_reranking: true
    enable_rag: false
    enable_caching: true
  
  publications_config:
    enable_pubmed: true
    enable_scholar: false    # Start with False, add later
    enable_citations: true
    enable_pdf_download: false
    enable_fulltext: false
    
    pubmed_config:
      api_key: ${NCBI_API_KEY}
      max_results: 50
  
  llm_config:
    # Start with basic LLM features
    enable_llm_reformulation: true
    enable_llm_embeddings: false
    enable_llm_reranking: false
    enable_synthesis: false
    enable_hypotheses: false
    
    reformulation_model:
      model_name: "BioMistral-7B"
      gpu_id: 0
      quantization: "8bit"
  
  integration_config:
    enable_cross_reference: true
    enable_unified_ranking: true
    enable_deduplication: true
    enable_entity_extraction: false
    enable_knowledge_graph: false
```

### **Incremental Adoption Path**

**Week 1-2: Publications (PubMed only)**
```yaml
enable_publications: true
publications_config:
  enable_pubmed: true
  enable_scholar: false
  enable_citations: false
```

**Week 3: Add Citations**
```yaml
publications_config:
  enable_pubmed: true
  enable_citations: true  # NEW
```

**Week 4: Add Scholar**
```yaml
publications_config:
  enable_pubmed: true
  enable_scholar: true    # NEW
  enable_citations: true
```

**Week 5: Add PDF**
```yaml
publications_config:
  enable_pdf_download: true  # NEW
  enable_fulltext: true      # NEW
```

**Week 6: LLM Query Enhancement**
```yaml
enable_llm: true
llm_config:
  enable_llm_reformulation: true  # NEW
```

**Week 7-8: LLM Reranking**
```yaml
llm_config:
  enable_llm_reformulation: true
  enable_llm_reranking: true     # NEW
```

**Week 9-10: Premium Features**
```yaml
llm_config:
  enable_synthesis: true         # NEW
  enable_hypotheses: true        # NEW
```

---

## 🔄 Migration from Original Plans

### **Original Plan Issues**

❌ **Issue 1: Too Many Modules**
```python
# Original: 7 new top-level modules
lib/publications/
lib/pdf/
lib/query/
lib/knowledge/
lib/integration/
lib/web/
lib/llm/
```

✅ **Refactored: 3 Consolidated Modules**
```python
lib/publications/  # Includes pdf/, web/ scraping
lib/llm/           # Includes query/ enhancement
lib/integration/   # Includes knowledge/ extraction
```

---

❌ **Issue 2: Flat Orchestration**
```python
# Original: SearchAgent manages 10+ components
class SearchAgent:
    def __init__(self):
        self.reformulator = BiomedicalQueryReformulator()
        self.pubmed = PubMedClient()
        self.scholar = GoogleScholarClient()
        self.pdf_scraper = WebPDFScraper()
        self.llm_embedder = AdvancedBiomedicalEmbeddings()
        self.llm_reranker = LLMReranker()
        self.synthesizer = MultiPaperSynthesizer()
        self.hypothesis_gen = HypothesisGenerator()
        self.geo_client = GEOClient()
        self.keyword_ranker = KeywordRanker()
        # ... messy!
```

✅ **Refactored: Pipeline Composition**
```python
class SearchAgent:
    def __init__(self, config):
        # Core (always)
        self.geo_client = GEOClient()
        self.keyword_ranker = KeywordRanker()
        
        # Optional pipelines (3-4 total)
        if config.enable_semantic:
            self.semantic_pipeline = AdvancedSearchPipeline()
        if config.enable_publications:
            self.publication_pipeline = PublicationSearchPipeline()
        if config.enable_llm:
            self.llm_pipeline = LLMEnhancedSearchPipeline()
        if config.enable_integration:
            self.integration_pipeline = IntegrationPipeline()
```

---

❌ **Issue 3: No Feature Toggles**
```python
# Original: All-or-nothing integration
class LLMEnhancedSearchAgent:
    def __init__(self):
        # Always initializes everything
        self.reformulator = BiomedicalQueryReformulator()
        self.llm_embedder = AdvancedBiomedicalEmbeddings()
        self.llm_reranker = LLMReranker()
```

✅ **Refactored: Feature Toggles**
```python
class LLMEnhancedSearchPipeline:
    def __init__(self, config):
        # Conditional initialization
        if config.enable_llm_reformulation:
            self.reformulator = BiomedicalQueryReformulator()
        if config.enable_llm_embeddings:
            self.llm_embedder = AdvancedBiomedicalEmbeddings()
        if config.enable_llm_reranking:
            self.llm_reranker = LLMReranker()
```

---

❌ **Issue 4: Mixed Responsibilities**
```python
# Original: SearchAgent does both datasets AND publications
class SearchAgent:
    def search(self, query):
        # Search datasets
        datasets = self.geo_client.search(query)
        # Search publications (mixed responsibility)
        publications = self.pubmed_client.search(query)
        # Mix results (unclear separation)
        return mix_results(datasets, publications)
```

✅ **Refactored: Clear Separation**
```python
class SearchAgent:
    def _process(self, input_data, context):
        # 1. Dataset search (core responsibility)
        dataset_results = self._search_datasets(input_data)
        
        # 2. Publication search (optional, delegated to pipeline)
        publication_results = None
        if self.publication_pipeline:
            publication_results = self.publication_pipeline.search(...)
        
        # 3. Integration (optional, delegated to pipeline)
        if self.integration_pipeline and publication_results:
            return self.integration_pipeline.integrate(
                dataset_results,
                publication_results
            )
        
        return dataset_results
```

---

## 📅 Refactored Implementation Timeline

### **Phase 1: Foundation (Week 1-2)**
**Goal:** Publication mining with PubMed

**Tasks:**
1. Create `lib/publications/` structure
2. Implement `PubMedClient`
3. Implement `PublicationSearchPipeline` (PubMed only)
4. Integrate with SearchAgent (add `enable_publications` flag)
5. Write tests
6. Deploy and validate

**Feature Toggles:**
```yaml
enable_publications: true
publications_config:
  enable_pubmed: true
  enable_scholar: false
  enable_citations: false
```

**Deliverables:**
- ✅ PubMed search working
- ✅ Publications integrated in SearchAgent
- ✅ Tests passing
- ✅ Documentation updated

---

### **Phase 2: Enhanced Publications (Week 3)**
**Goal:** Add citations and Google Scholar

**Tasks:**
1. Implement `CitationAnalyzer`
2. Implement `GoogleScholarClient`
3. Update `PublicationSearchPipeline`
4. Add feature toggles
5. Write tests

**Feature Toggles:**
```yaml
publications_config:
  enable_pubmed: true
  enable_scholar: true     # NEW
  enable_citations: true   # NEW
```

---

### **Phase 3: PDF Processing (Week 4)**
**Goal:** PDF download and full-text extraction

**Tasks:**
1. Implement `PDFDownloader`
2. Implement `FullTextExtractor` (GROBID)
3. Update `PublicationSearchPipeline`
4. Add feature toggles
5. Write tests

**Feature Toggles:**
```yaml
publications_config:
  enable_pdf_download: true   # NEW
  enable_fulltext: true       # NEW
```

---

### **Phase 4: LLM Foundation (Week 5-6)**
**Goal:** Query reformulation and LLM embeddings

**Tasks:**
1. Create `lib/llm/` structure
2. Implement `BiomedicalQueryReformulator` (BioMistral-7B)
3. Implement `AdvancedBiomedicalEmbeddings` (E5-Mistral-7B)
4. Create `LLMEnhancedSearchPipeline`
5. Integrate with SearchAgent (add `enable_llm` flag)
6. GPU allocation and testing

**Feature Toggles:**
```yaml
enable_llm: true
llm_config:
  enable_llm_reformulation: true
  enable_llm_embeddings: true
```

---

### **Phase 5: LLM Reranking (Week 7)**
**Goal:** Explainable LLM reranking

**Tasks:**
1. Implement `LLMReranker` (Llama-3.1-8B)
2. Add explainability features
3. Update `LLMEnhancedSearchPipeline`
4. Add feature toggle
5. Write tests

**Feature Toggles:**
```yaml
llm_config:
  enable_llm_reranking: true   # NEW
```

---

### **Phase 6: Integration (Week 8)**
**Goal:** Multi-source integration

**Tasks:**
1. Create `lib/integration/` structure
2. Implement `UnifiedRanker`
3. Implement `CrossSourceDeduplicator`
4. Create `IntegrationPipeline`
5. Integrate with SearchAgent (add `enable_integration` flag)

**Feature Toggles:**
```yaml
enable_integration: true
integration_config:
  enable_unified_ranking: true
  enable_deduplication: true
```

---

### **Phase 7: Synthesis (Week 9)**
**Goal:** Multi-paper synthesis

**Tasks:**
1. Implement `MultiPaperSynthesizer` (Meditron-70B)
2. Update `LLMEnhancedSearchPipeline`
3. Add feature toggle
4. GPU allocation (2 GPUs)
5. Write tests

**Feature Toggles:**
```yaml
llm_config:
  enable_synthesis: true   # NEW
```

---

### **Phase 8: Premium Features (Week 10)**
**Goal:** Hypothesis generation

**Tasks:**
1. Implement `HypothesisGenerator` (Falcon-180B)
2. Update `LLMEnhancedSearchPipeline`
3. Add feature toggle
4. GPU allocation (H100 cluster)
5. Write tests

**Feature Toggles:**
```yaml
llm_config:
  enable_hypotheses: true   # NEW
```

---

## ✅ Validation Checklist

### **Architecture Alignment** ✅

- [x] All pipelines follow `AdvancedSearchPipeline` pattern
- [x] Feature toggles for every enhancement
- [x] Configuration dataclasses for all components
- [x] Composition over inheritance maintained
- [x] Clean separation (agents/ vs lib/)

### **Modularity Preserved** ✅

- [x] Consolidated to 3 new modules (not 7)
- [x] Each module has clear responsibility
- [x] No circular dependencies
- [x] Plug-and-play components

### **Simplicity Maintained** ✅

- [x] SearchAgent manages ≤4 pipelines (not 10+ components)
- [x] Each pipeline is self-contained
- [x] Linear execution flow in each pipeline
- [x] Easy to understand and test

### **Incremental Adoption** ✅

- [x] Can enable features one by one
- [x] Feature toggles default to False (backwards compatible)
- [x] Each phase adds independent value
- [x] No breaking changes to existing code

### **Phase-wise Implementation** ✅

- [x] Week 1-2: Publications (PubMed)
- [x] Week 3: Enhanced publications (Scholar, citations)
- [x] Week 4: PDF processing
- [x] Week 5-6: LLM query enhancement
- [x] Week 7: LLM reranking
- [x] Week 8: Integration
- [x] Week 9: Synthesis
- [x] Week 10: Hypotheses

---

## 🎯 Key Takeaways

### **What Changed**

1. **Module Organization:**
   - ❌ 7 new modules → ✅ 3 consolidated modules

2. **Integration Approach:**
   - ❌ Flat orchestration → ✅ Pipeline composition

3. **Feature Enablement:**
   - ❌ All-or-nothing → ✅ Feature toggles

4. **Agent Responsibilities:**
   - ❌ Mixed dataset + publication search → ✅ Clear separation with pipelines

5. **Pattern Compliance:**
   - ❌ New patterns introduced → ✅ Follows existing AdvancedSearchPipeline pattern

### **What Stayed the Same**

✅ **All component designs** - PubMedClient, GoogleScholarClient, etc. remain as designed  
✅ **All functionality** - Every planned feature is still included  
✅ **All LLM innovations** - Query reformulation, embeddings, reranking, synthesis, hypotheses  
✅ **Implementation timeline** - Still 10 weeks, same deliverables  
✅ **Performance targets** - +150% coverage, +40% accuracy, etc.  

### **What Got Better**

⭐ **Modularity** - Fewer, better-organized modules  
⭐ **Simplicity** - Pipeline composition vs flat orchestration  
⭐ **Flexibility** - Feature toggles enable incremental adoption  
⭐ **Maintainability** - Follows existing proven patterns  
⭐ **Testability** - Each pipeline independently testable  
⭐ **Architecture alignment** - Perfectly fits existing codebase  

---

## 📝 Next Steps

1. **Review this refactored strategy** with user
2. **Confirm alignment** with "modular and plug and play" goals
3. **Validate** simplicity vs original plans
4. **Approve** implementation approach
5. **Begin Week 1** implementation (Publications module)

---

**Refactored Strategy Status:** ✅ Complete and Architecture-Aligned  
**Ready for Implementation:** Yes - following proven AdvancedSearchPipeline pattern  
**Risk Level:** Low - incremental, feature-toggle driven approach
