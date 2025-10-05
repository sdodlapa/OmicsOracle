# OmicsOracle Search System: Technical Documentation

## Executive Summary

The OmicsOracle search system is designed to provide robust, intelligent search capabilities for biomedical data, particularly focusing on genomic datasets from sources like GEO (Gene Expression Omnibus). This document details the architecture, components, and flow of the search system, with particular emphasis on the trace capabilities that allow for debugging, monitoring, and optimization.

## 1. Introduction

### 1.1 Purpose

This document describes the technical implementation of the OmicsOracle search system, including its query processing flow, component architecture, and tracing capabilities. It serves as both a reference for developers working on the system and as a technical explanation for stakeholders interested in understanding how the system works.

### 1.2 Scope

The document covers:
- The core search pipeline architecture
- Enhanced query handling components
- The query tracing system
- Testing and validation framework
- Current limitations and future enhancements

### 1.3 Intended Audience

This document is intended for:
- Software developers maintaining or extending the system
- Technical stakeholders evaluating the system
- Data scientists interested in understanding how queries are processed
- Researchers using the system who want deeper insights into the search process

## 2. System Overview

### 2.1 Architecture

The OmicsOracle search system consists of several key components:

1. **Frontend Interface**: Web UI and API endpoints for submitting queries
2. **Query Parser**: Extracts components from natural language queries
3. **Biomedical Synonym Expander**: Enhances queries with domain-specific synonyms
4. **Multi-Strategy Search Engine**: Attempts various query strategies to find results
5. **Pipeline Connector**: Interfaces with the NCBI/GEO data pipeline
6. **Results Formatter**: Structures results for presentation
7. **Query Tracer**: Records and analyzes the entire query flow

### 2.2 Data Flow

1. User submits a query through web interface or API
2. Query parser breaks down the query into components (disease, tissue, organism, data type)
3. Synonym expander enhances components with relevant biomedical terminology
4. Multi-strategy search engine attempts the original query
5. If needed, alternative queries are generated and attempted
6. Results are retrieved from GEO and other sources
7. Results are formatted and returned to the user
8. The entire process is recorded by the query tracer

### 2.3 Key Technologies

- **Backend**: Python 3.11+, FastAPI
- **Data Processing**: BioPython, LangChain
- **Caching**: Redis, ChromaDB
- **Tracing**: Custom QueryTracer module
- **Testing**: Pytest, custom validation framework

## 3. Query Parsing and Enhancement

### 3.1 Query Parser

The `QueryParser` class is responsible for breaking down complex biomedical queries into structured components that can be more effectively processed.

#### 3.1.1 Component Extraction

The parser identifies key components in natural language queries:

- **Organism**: human, mouse, rat, etc.
- **Disease**: cancer, diabetes, Alzheimer's, etc.
- **Tissue**: liver, brain, lung, etc.
- **Data Type**: RNA-seq, microarray, gene expression, etc.

Example:
```python
# Query: "gene expression data for liver cancer of human species"
components = {
    "organism": "human",
    "disease": "cancer",
    "tissue": "liver",
    "data_type": "gene expression"
}
```

#### 3.1.2 Implementation Details

The parser uses regular expression patterns to identify biomedical entities:

```python
self.patterns = {
    'organism': [
        r'(?:human|homo sapiens|patient|patients)',
        r'(?:mouse|mice|mus musculus)',
        # Additional patterns...
    ],
    'disease': [
        r'(?:cancer|carcinoma|tumor|tumour|neoplasm)',
        r'(?:diabetes|diabetic)',
        # Additional patterns...
    ],
    # Additional components...
}
```

### 3.2 Biomedical Synonym Expander

The `BiomedicalSynonymExpander` class enriches query components with domain-specific synonyms to improve search recall.

#### 3.2.1 Synonym Dictionaries

The expander maintains dictionaries of synonyms for various biomedical concepts:

- **Disease synonyms**: Maps diseases to common alternative terms
- **Tissue synonyms**: Maps tissues to anatomical alternatives
- **Organism synonyms**: Maps organisms to scientific and common names
- **Data type synonyms**: Maps data types to technical alternatives

Example:
```python
self.disease_synonyms = {
    'cancer': ['tumor', 'tumour', 'neoplasm', 'malignancy', 'carcinoma'],
    'liver cancer': ['hepatocellular carcinoma', 'HCC', 'hepatic cancer'],
    # Additional mappings...
}
```

#### 3.2.2 Expansion Process

The expansion process:

1. Takes extracted components as input
2. For each component, looks up direct and partial matches in synonym dictionaries
3. Returns expanded sets of terms for each component

Example:
```python
# For "liver cancer":
expanded_terms = {
    'liver cancer', 'hepatocellular carcinoma', 'HCC', 'hepatic cancer'
}
```

### 3.3 Alternative Query Generation

The search system generates alternative queries to try if the original query doesn't yield satisfactory results.

#### 3.3.1 Generation Strategy

Alternative queries are generated by:

1. Combining expanded synonyms in various combinations
2. Prioritizing combinations of data type + disease/tissue
3. Including organism information in more specific queries
4. Limiting the total number of alternatives to prevent excessive searches

#### 3.3.2 Query Prioritization

Queries are prioritized by:
- Number of components included (more is better)
- Component types included (disease and data type prioritized)
- Length of query (to include more specific information)

## 4. Search Execution

### 4.1 Multi-Strategy Search

The `perform_multi_strategy_search` function orchestrates the search process, employing multiple strategies to find relevant results.

#### 4.1.1 Strategy Flow

1. Try the original query first
2. If insufficient results, try generated alternative queries
3. Track queries already attempted to avoid duplication
4. Return results from the first successful strategy

#### 4.1.2 Result Metadata

The search function returns not just results but also metadata about the search process:

```python
return result.geo_ids, {
    'metadata': result.metadata,
    'ai_summaries': result.ai_summaries,
    'components': components,
    'expanded_components': expanded_components,
    'search_strategy': 'alternative',
    'query_used': alt_query,
    'original_query': query
}
```

### 4.2 Pipeline Integration

The search system integrates with the OmicsOracle pipeline to retrieve and process data from external sources.

#### 4.2.1 Pipeline Interface

The search function interfaces with the pipeline through the `process_query` method:

```python
result = await pipeline.process_query(query, max_results=max_results)
```

#### 4.2.2 Progress Tracking

The pipeline provides progress callbacks to track long-running operations:

```python
@tracer.trace_function("progress")
async def progress_callback(query_id, event):
    tracer.record_step(
        "progress",
        f"pipeline.{event.stage}",
        {"query_id": query_id, "message": event.message},
        {"percentage": event.percentage, "detail": event.detail},
        status="progress"
    )
```

## 5. Query Tracing System

### 5.1 Tracer Architecture

The `QueryTracer` class provides comprehensive tracing of the entire query flow from submission to result rendering.

#### 5.1.1 Tracing Context

The tracer uses context managers to track different phases of the query processing:

```python
with tracer.trace_context("search", "pipeline_processing"):
    # Search operations recorded in this context
```

#### 5.1.2 Step Recording

Individual steps within each context are recorded with detailed information:

```python
tracer.record_step(
    "search",
    "enhanced_search",
    {"query": query, "max_results": max_results},
    {"geo_ids": geo_ids, "metadata_info": metadata_info}
)
```

### 5.2 Trace Reports

The tracer generates comprehensive reports in both JSON and Markdown formats.

#### 5.2.1 Report Structure

Markdown reports include:
- Query information (original query, timestamps, duration)
- Results summary (GEO IDs found)
- Component performance metrics
- Detailed execution steps with inputs and outputs
- Transformations and decisions made during processing
- Error and warning information

#### 5.2.2 Report Generation

Reports are generated through the `generate_report` method and saved to the specified output directory:

```python
report_path = tracer.generate_report()
```

### 5.3 Trace Analysis

The trace data can be analyzed to:
- Identify performance bottlenecks
- Understand which query strategies are most effective
- Debug failed searches
- Optimize component extraction and synonym expansion

## 6. Testing and Validation Framework

### 6.1 Comprehensive Testing Suite

The OmicsOracle testing framework includes specialized components for validating the search system.

#### 6.1.1 Test Components

- `test_endpoints_comprehensive.py`: Tests all API endpoints including enhanced query endpoints
- `validate_enhanced_query_handler.py`: Validates query parsing, synonym expansion, and alternative query generation
- `run_comprehensive_tests_and_traces.py`: Runs all tests and generates trace reports
- `run_all_tests.sh`: Orchestrates the entire testing process

#### 6.1.2 Test Coverage

The testing suite covers:
- API endpoint functionality
- Enhanced query handling
- Component extraction accuracy
- Synonym expansion correctness
- Alternative query generation quality
- Multi-strategy search effectiveness

### 6.2 Validation Methodology

The validation process includes:

#### 6.2.1 Component Extraction Validation

Tests that the system correctly identifies biomedical components in queries:

```python
def test_component_extraction(queries):
    results = []
    parser = QueryParser()

    for query in queries:
        components = parser.parse_query(query)
        # Validation logic...

    return results
```

#### 6.2.2 Synonym Expansion Validation

Tests that synonyms are correctly expanded for various biomedical terms:

```python
def test_synonym_expansion(queries):
    results = []
    parser = QueryParser()
    expander = BiomedicalSynonymExpander()

    for query in queries:
        components = parser.parse_query(query)
        expanded = expander.expand_query_components(components)
        # Validation logic...

    return results
```

#### 6.2.3 End-to-End Validation

Tests the entire search flow from query to results:

```python
async def test_full_enhanced_search(queries, max_results=5):
    results = []
    config = Config()
    pipeline = OmicsOracle(config)

    for query in queries:
        geo_ids, metadata = await perform_multi_strategy_search(
            pipeline, query, max_results=max_results
        )
        # Validation logic...

    return results
```

### 6.3 Validation Reports

The validation process generates detailed reports:

- Markdown reports documenting validation results
- JSON data files containing detailed validation metrics
- Test summary reports aggregating all validation results

## 7. Performance Considerations

### 7.1 Current Performance Metrics

Based on trace reports, the current performance metrics are:

- Pipeline initialization: 8-9 seconds
- Query parsing: <0.001 seconds
- Synonym expansion: <0.001 seconds
- Alternative query generation: <0.001 seconds
- Search execution: 0.2-4.2 seconds (varies by query)
- Total query processing: 9-13 seconds

### 7.2 Optimization Opportunities

Potential areas for optimization include:

- Pipeline initialization caching
- Precomputed synonym expansions for common terms
- Parallel execution of alternative queries
- More efficient GEO API interactions
- Result caching for common queries

## 8. Current Limitations and Future Enhancements

### 8.1 Current Limitations

- Limited synonym dictionaries for highly specialized terms
- No personalization of search results based on user history
- Alternative query generation can sometimes produce redundant queries
- Limited handling of complex boolean expressions in queries

### 8.2 Planned Enhancements

- Machine learning-based component extraction
- Dynamic synonym expansion based on recent literature
- User feedback incorporation into search strategy
- More sophisticated result ranking algorithms
- Real-time performance optimization based on trace analysis

## 9. Conclusion

The OmicsOracle search system represents a sophisticated approach to biomedical data retrieval, combining domain-specific knowledge with flexible search strategies. The comprehensive tracing capabilities provide valuable insights into the system's behavior, enabling continuous improvement and optimization.

The modular architecture allows for future enhancements while maintaining backward compatibility, ensuring that the system can evolve to meet changing requirements and incorporate new technologies as they become available.

## Appendix A: Code Examples

### QueryParser

```python
class QueryParser:
    def __init__(self):
        # Pattern initialization...

    def parse_query(self, query: str) -> Dict[str, Optional[str]]:
        """Parse a complex query into components for structured search."""
        # Implementation...

    def generate_alternative_queries(self, components: Dict[str, Optional[str]]) -> List[str]:
        """Generate alternative simpler queries based on the parsed components."""
        # Implementation...
```

### BiomedicalSynonymExpander

```python
class BiomedicalSynonymExpander:
    def __init__(self):
        # Synonym dictionary initialization...

    def expand_term(self, term: str, category: str) -> Set[str]:
        """Expand a biomedical term with its synonyms."""
        # Implementation...

    def expand_query_components(self, components: Dict[str, Optional[str]]) -> Dict[str, Set[str]]:
        """Expand all components in a parsed query with synonyms."""
        # Implementation...
```

### Multi-Strategy Search

```python
async def perform_multi_strategy_search(pipeline, query: str, max_results: int = 10) -> Tuple[List[str], Dict[str, Any]]:
    """Perform a multi-strategy search that breaks down complex queries and tries multiple approaches."""
    # Implementation...
```

## Appendix B: Sample Trace Report

```markdown
# Query Trace Report: trace_20250627_140215

## Query Information

- **Original Query**: `breast cancer gene expression in humans`
- **Start Time**: 2025-06-27T14:02:15.159213
- **End Time**: 2025-06-27T14:02:24.342422
- **Duration**: 9.183 seconds
- **Status**: completed

## Results Summary

- **GEO IDs Found**: 10
  - GSE119937, GSE99699, GSE83292, GSE68085, GSE35019, GSE27584, GSE17041, GSE15309, GSE1902, GSE14

## Component Performance

| Component | Calls | Total Time (s) | Avg Time (s) | Max Time (s) |
|-----------|-------|---------------|--------------|-------------|
| config | 1 | 0.000 | 0.000 | 0.000 |
| pipeline | 1 | 8.941 | 8.941 | 8.941 |
| query_analyzer | 1 | 0.001 | 0.001 | 0.001 |
| pipeline_processing | 1 | 0.240 | 0.240 | 0.240 |
| frontend_adapter | 1 | 0.001 | 0.001 | 0.001 |
| results_rendering | 1 | 0.000 | 0.000 | 0.000 |

## Execution Steps

### ✅ Step 1: initialization - config
...

### ✅ Step 2: initialization - pipeline
...

### ✅ Step 3: query_parsing - component_extraction
...
```

## Appendix C: Glossary

- **GEO**: Gene Expression Omnibus, a public functional genomics data repository
- **Component Extraction**: The process of identifying key biomedical entities in a query
- **Synonym Expansion**: The process of enriching query terms with equivalent medical terminology
- **Multi-Strategy Search**: A search approach that tries multiple query variations to find optimal results
- **Query Tracing**: Detailed recording of each step in the query processing pipeline
- **Alternative Query**: A reformulated version of the original query using different terminology

---

*Document Version: 1.0*
*Last Updated: June 27, 2025*
*Document Maintainer: OmicsOracle Development Team*
