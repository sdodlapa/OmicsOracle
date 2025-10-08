# Agent Framework Guide

**Complete guide to the OmicsOracle v2 Multi-Agent Framework**

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Architecture Overview](#architecture-overview)
4. [Agent Reference](#agent-reference)
5. [Workflow Patterns](#workflow-patterns)
6. [Customization](#customization)
7. [Troubleshooting](#troubleshooting)
8. [Performance Tips](#performance-tips)

---

## Introduction

The OmicsOracle v2 Agent Framework is a sophisticated multi-agent system designed to handle complex biomedical research queries through coordinated agent collaboration. Each agent specializes in a specific task, and they work together to provide comprehensive analysis of genomic datasets.

### Why Multi-Agent Architecture?

- **Separation of Concerns**: Each agent has a single, well-defined responsibility
- **Modularity**: Agents can be developed, tested, and deployed independently
- **Scalability**: Easy to add new agents or enhance existing ones
- **Testability**: Each agent can be thoroughly unit tested in isolation
- **Maintainability**: Changes to one agent don't affect others

### Key Features

- ✅ **5 Specialized Agents**: Query, Search, Data, Report, and Orchestrator
- ✅ **149 Unit Tests**: 100% passing with high coverage
- ✅ **24 Integration Tests**: End-to-end workflow validation
- ✅ **Flexible Workflows**: Multiple workflow patterns for different use cases
- ✅ **Error Handling**: Robust error recovery and graceful degradation
- ✅ **Performance Optimized**: Caching, rate limiting, and async operations

---

## Getting Started

### Prerequisites

```bash
# Python 3.11+
python --version

# Install dependencies
pip install -r requirements.txt

# Download NLP model
python -m spacy download en_core_sci_sm
```

### Quick Start Example

```python
from omics_oracle_v2.agents import Orchestrator
from omics_oracle_v2.agents.models.orchestrator import (
    OrchestratorInput,
    WorkflowType,
)
from omics_oracle_v2.core import Settings, GEOSettings

# Configure settings
settings = Settings(
    debug=True,
    geo=GEOSettings(
        ncbi_email="your.email@example.com",  # Required for NCBI API
    ),
)

# Create orchestrator
orchestrator = Orchestrator(settings=settings)

# Execute a simple workflow
workflow_input = OrchestratorInput(
    query="Find TP53 datasets in breast cancer research",
    workflow_type=WorkflowType.SIMPLE_SEARCH,
    max_results=10,
)

result = orchestrator.execute(workflow_input)

if result.success:
    print(f"Found {result.output.total_datasets_found} datasets")
    print(f"Generated report: {result.output.final_report[:200]}...")
else:
    print(f"Error: {result.error}")
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run agent unit tests
pytest tests/unit/agents/

# Run integration tests
pytest tests/integration/

# Check coverage
pytest --cov=omics_oracle_v2 --cov-report=html
```

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Orchestrator Agent                     │
│  (Coordinates agent collaboration & workflow execution)  │
└────────────┬────────────────────────────────────────────┘
             │
     ┌───────┴────────┬──────────┬──────────┬─────────┐
     ▼                ▼          ▼          ▼         ▼
┌─────────┐    ┌──────────┐  ┌──────┐  ┌────────┐  ┌────────┐
│ Query   │    │ Search   │  │ Data │  │Report  │  │ (More  │
│ Agent   │───>│ Agent    │─>│Agent │─>│Agent   │  │Agents) │
│(NLP)    │    │(GEO)     │  │(QA)  │  │(AI)    │  │        │
└─────────┘    └──────────┘  └──────┘  └────────┘  └────────┘
```

### Agent Lifecycle

```
IDLE ─> PROCESSING ─> COMPLETED ─> IDLE
  │         │             │
  │         └─> FAILED ───┘
  │               │
  └───────────────┘
```

### Data Flow

1. **User Query** → QueryAgent (NLP entity extraction)
2. **Search Terms** → SearchAgent (GEO database search)
3. **Datasets** → DataAgent (Quality validation)
4. **Processed Datasets** → ReportAgent (AI-powered synthesis)
5. **Final Report** → User

---

## Agent Reference

### 1. QueryAgent

**Purpose**: Process natural language queries using NLP to extract biomedical entities.

**Key Features**:
- Biomedical named entity recognition (genes, diseases, chemicals, etc.)
- Intent classification (search, analyze, summarize, compare)
- Synonym expansion using MeSH/UMLS
- Search term generation
- Confidence scoring

**Input**: `QueryInput`
```python
QueryInput(
    query="Find TP53 mutations in breast cancer",
    max_entities=100,
    include_synonyms=True,
    confidence_threshold=0.7,
)
```

**Output**: `QueryOutput`
- `original_query`: The input query
- `intent`: Detected user intent
- `entities`: Extracted biomedical entities
- `search_terms`: Generated search terms
- `entity_counts`: Count by entity type
- `confidence`: Confidence in query understanding

**Example**:
```python
from omics_oracle_v2.agents import QueryAgent
from omics_oracle_v2.agents.models import QueryInput

agent = QueryAgent()
result = agent.execute(QueryInput(
    query="Find BRCA1 mutations in ovarian cancer patients"
))

print(f"Entities found: {len(result.output.entities)}")
print(f"Search terms: {result.output.search_terms}")
```

**Performance**: < 10s (includes NLP model loading)

---

### 2. SearchAgent

**Purpose**: Search GEO database for relevant datasets using extracted search terms.

**Key Features**:
- NCBI E-utilities integration
- Relevance ranking based on term matches
- Metadata extraction (organism, samples, platform, etc.)
- Filtering by organism, study type, sample count
- Rate limiting and caching

**Input**: `SearchInput`
```python
SearchInput(
    search_terms=["TP53", "breast cancer"],
    max_results=50,
    organism="Homo sapiens",
    study_type="Expression profiling by array",
    min_samples=10,
)
```

**Output**: `SearchOutput`
- `datasets`: List of `RankedDataset` objects
- `total_found`: Total matching datasets
- `search_terms_used`: Terms used in search
- `filters_applied`: Active filters

**Example**:
```python
from omics_oracle_v2.agents import SearchAgent
from omics_oracle_v2.agents.models.search import SearchInput

agent = SearchAgent()
result = agent.execute(SearchInput(
    search_terms=["cancer", "gene expression"],
    max_results=20,
    organism="Homo sapiens",
))

print(f"Found {result.output.total_found} datasets")
for dataset in result.output.datasets[:5]:
    print(f"- {dataset.dataset.geo_id}: {dataset.relevance_score:.2f}")
```

**Performance**: < 10s (first search), < 1s (cached)

---

### 3. DataAgent

**Purpose**: Validate and process dataset metadata, assess quality.

**Key Features**:
- Quality scoring algorithm
- Publication validation (PubMed)
- SRA data availability check
- Age calculation
- Quality level classification (excellent/good/fair/poor)

**Input**: `DataInput`
```python
DataInput(
    datasets=[ranked_dataset1, ranked_dataset2, ...],
    min_quality_score=0.5,
    require_publication=False,
    require_sra=False,
)
```

**Output**: `DataOutput`
- `processed_datasets`: List of `ProcessedDataset` with quality metrics
- `total_processed`: Count of datasets processed
- `total_passed_quality`: Count passing quality threshold
- `average_quality_score`: Mean quality score
- `quality_distribution`: Distribution by quality level

**Example**:
```python
from omics_oracle_v2.agents import DataAgent
from omics_oracle_v2.agents.models.data import DataInput

agent = DataAgent()
result = agent.execute(DataInput(
    datasets=search_results,
    min_quality_score=0.7,
))

high_quality = result.output.get_high_quality_datasets()
print(f"High quality datasets: {len(high_quality)}")
```

**Performance**: < 2s

---

### 4. ReportAgent

**Purpose**: Generate comprehensive AI-powered reports from processed datasets.

**Key Features**:
- GPT-4 integration for natural language synthesis
- Multiple report types (brief, comprehensive, technical, executive)
- Multiple output formats (markdown, JSON, HTML, text)
- Key insight extraction
- Actionable recommendations
- Quality summary

**Input**: `ReportInput`
```python
ReportInput(
    datasets=[processed_dataset1, processed_dataset2, ...],
    query_context="Original user query",
    report_type=ReportType.COMPREHENSIVE,
    report_format=ReportFormat.MARKDOWN,
    max_datasets=10,
    include_quality_analysis=True,
    include_recommendations=True,
)
```

**Output**: `ReportOutput`
- `full_report`: Complete formatted report
- `title`: Report title
- `summary`: Executive summary
- `sections`: Structured report sections
- `key_insights`: Extracted insights
- `recommendations`: Actionable next steps

**Example**:
```python
from omics_oracle_v2.agents import ReportAgent
from omics_oracle_v2.agents.models.report import (
    ReportInput,
    ReportType,
    ReportFormat,
)

agent = ReportAgent()
result = agent.execute(ReportInput(
    datasets=processed_datasets,
    query_context="TP53 in breast cancer",
    report_type=ReportType.COMPREHENSIVE,
    report_format=ReportFormat.MARKDOWN,
))

print(result.output.full_report)
```

**Performance**: < 10s (depends on OpenAI API)

---

### 5. Orchestrator

**Purpose**: Coordinate multi-agent workflows and manage execution.

**Key Features**:
- 4 workflow types (SIMPLE_SEARCH, FULL_ANALYSIS, QUICK_REPORT, DATA_VALIDATION)
- 7-stage workflow lifecycle
- Per-stage result tracking
- Error handling and recovery
- Execution time monitoring

**Input**: `OrchestratorInput`
```python
OrchestratorInput(
    query="Find cancer datasets",
    workflow_type=WorkflowType.FULL_ANALYSIS,
    max_results=10,
    organism="Homo sapiens",
    min_samples=50,
    report_format=ReportFormat.MARKDOWN,
)
```

**Output**: `OrchestratorOutput`
- `final_stage`: Last completed stage
- `success`: Overall workflow success
- `stage_results`: Results from each stage
- `final_report`: Generated report (if applicable)
- `total_datasets_found`: Dataset count
- `total_execution_time_ms`: Total time

**Workflow Types**:

1. **SIMPLE_SEARCH**: Query → Search → Report
2. **FULL_ANALYSIS**: Query → Search → Data → Report
3. **QUICK_REPORT**: Generate report from dataset IDs (not implemented)
4. **DATA_VALIDATION**: Validate existing datasets (not implemented)

**Example**:
```python
from omics_oracle_v2.agents import Orchestrator
from omics_oracle_v2.agents.models.orchestrator import (
    OrchestratorInput,
    WorkflowType,
)

orchestrator = Orchestrator()
result = orchestrator.execute(OrchestratorInput(
    query="BRCA1 mutations in cancer",
    workflow_type=WorkflowType.FULL_ANALYSIS,
    max_results=10,
))

# Check execution
print(f"Workflow completed: {result.output.final_stage}")
print(f"Stages completed: {result.output.stages_completed}")
print(f"Execution time: {result.output.total_execution_time_ms}ms")
```

**Performance**: < 30s (full pipeline)

---

## Workflow Patterns

### Pattern 1: Simple Search

**Use Case**: Quick dataset discovery without deep analysis.

```python
# Query -> Search -> Report
orchestrator_input = OrchestratorInput(
    query="Find TP53 datasets",
    workflow_type=WorkflowType.SIMPLE_SEARCH,
    max_results=20,
)

result = orchestrator.execute(orchestrator_input)
```

**Stages**: QUERY_PROCESSING → DATASET_SEARCH → REPORT_GENERATION → COMPLETED

### Pattern 2: Full Analysis

**Use Case**: Comprehensive analysis with quality validation.

```python
# Query -> Search -> Data -> Report
orchestrator_input = OrchestratorInput(
    query="Analyze cancer gene expression datasets",
    workflow_type=WorkflowType.FULL_ANALYSIS,
    max_results=10,
    min_samples=50,
)

result = orchestrator.execute(orchestrator_input)
```

**Stages**: QUERY_PROCESSING → DATASET_SEARCH → DATA_VALIDATION → REPORT_GENERATION → COMPLETED

### Pattern 3: Entity-Focused Search

**Use Case**: Find datasets for specific biomedical entities.

```python
# Focus on extracting and searching for specific genes/diseases
orchestrator_input = OrchestratorInput(
    query="BRCA1 and BRCA2 mutations in ovarian cancer patients",
    workflow_type=WorkflowType.FULL_ANALYSIS,
    max_results=15,
)

result = orchestrator.execute(orchestrator_input)

# Extract entities from query stage
query_stage = result.output.get_stage_result(WorkflowStage.QUERY_PROCESSING)
if query_stage and query_stage.success:
    entities = query_stage.output.entities
    print(f"Found entities: {[e.text for e in entities]}")
```

### Pattern 4: Quality-Focused Search

**Use Case**: Only high-quality datasets with publications.

```python
# Manual workflow for fine-grained control
query_agent = QueryAgent()
search_agent = SearchAgent()
data_agent = DataAgent()
report_agent = ReportAgent()

# 1. Process query
query_result = query_agent.execute(QueryInput(query="cancer research"))

# 2. Search with filters
search_result = search_agent.execute(SearchInput(
    search_terms=query_result.output.search_terms,
    max_results=50,
    organism="Homo sapiens",
    min_samples=100,
))

# 3. Strict quality filtering
data_result = data_agent.execute(DataInput(
    datasets=search_result.output.datasets,
    min_quality_score=0.8,
    require_publication=True,
))

# 4. Generate report
if len(data_result.output.processed_datasets) > 0:
    report_result = report_agent.execute(ReportInput(
        datasets=data_result.output.processed_datasets,
        report_type=ReportType.TECHNICAL,
    ))
```

### Pattern 5: Batch Processing

**Use Case**: Process multiple queries efficiently.

```python
queries = [
    "TP53 in breast cancer",
    "BRCA1 mutations",
    "EGFR in lung cancer",
]

results = []
for query in queries:
    result = orchestrator.execute(OrchestratorInput(
        query=query,
        workflow_type=WorkflowType.SIMPLE_SEARCH,
        max_results=10,
    ))
    results.append(result)

# Analyze results
successful = [r for r in results if r.success]
print(f"Processed {len(successful)}/{len(queries)} queries successfully")
```

---

## Customization

### Creating Custom Agents

Extend the base `Agent` class to create custom agents:

```python
from typing import List
from pydantic import BaseModel, Field
from omics_oracle_v2.agents.base import Agent

# Define input/output models
class CustomInput(BaseModel):
    data: List[str] = Field(..., description="Input data")

class CustomOutput(BaseModel):
    result: str = Field(..., description="Processing result")

# Create custom agent
class CustomAgent(Agent[CustomInput, CustomOutput]):
    """Custom agent for specialized processing."""

    def _validate_input(self, input_data: CustomInput) -> None:
        """Validate input data."""
        if not input_data.data:
            raise ValueError("Input data cannot be empty")

    def _process(self, input_data: CustomInput) -> CustomOutput:
        """Process input and generate output."""
        # Your custom logic here
        processed = " ".join(input_data.data)
        return CustomOutput(result=processed)

    def cleanup(self) -> None:
        """Clean up resources."""
        pass

# Use custom agent
agent = CustomAgent()
result = agent.execute(CustomInput(data=["hello", "world"]))
print(result.output.result)  # "hello world"
```

### Custom Workflow

Create custom workflows by combining agents:

```python
def custom_workflow(query: str) -> dict:
    """Custom workflow with specialized logic."""
    # Initialize agents
    query_agent = QueryAgent()
    search_agent = SearchAgent()

    # Step 1: Process query
    query_result = query_agent.execute(QueryInput(query=query))

    if not query_result.success:
        return {"error": query_result.error}

    # Step 2: Custom filtering logic
    gene_entities = [
        e for e in query_result.output.entities
        if e.entity_type == EntityType.GENE
    ]

    if not gene_entities:
        return {"error": "No gene entities found"}

    # Step 3: Targeted search
    search_result = search_agent.execute(SearchInput(
        search_terms=[e.text for e in gene_entities],
        max_results=10,
    ))

    return {
        "genes": [e.text for e in gene_entities],
        "datasets": search_result.output.total_found,
        "success": True,
    }
```

---

## Troubleshooting

### Common Issues

#### 1. NCBI Email Not Configured

**Error**: `NCBI client not available - check email configuration`

**Solution**:
```python
from omics_oracle_v2.core import Settings, GEOSettings

settings = Settings(
    geo=GEOSettings(
        ncbi_email="your.email@example.com",  # REQUIRED
    )
)
```

#### 2. OpenAI API Key Missing

**Error**: `OpenAI API key not configured`

**Solution**:
```bash
export OPENAI_API_KEY="sk-..."
```

Or in code:
```python
from omics_oracle_v2.core import Settings, AISettings

settings = Settings(
    ai=AISettings(
        api_key="sk-...",
    )
)
```

#### 3. NLP Model Not Found

**Error**: `Can't find model 'en_core_sci_sm'`

**Solution**:
```bash
python -m spacy download en_core_sci_sm
```

#### 4. SSL Certificate Errors

**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution** (for development only):
```python
settings = Settings(
    geo=GEOSettings(
        verify_ssl=False,  # Disable SSL verification
    )
)
```

#### 5. Rate Limiting

**Error**: `Rate limit exceeded`

**Solution**:
```python
settings = Settings(
    geo=GEOSettings(
        rate_limit=3,  # Requests per second (default: 3)
        max_retries=5,  # Retry attempts (default: 3)
    )
)
```

### Debugging Tips

1. **Enable Debug Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

settings = Settings(debug=True, log_level="DEBUG")
```

2. **Check Agent State**:
```python
result = agent.execute(input_data)
print(f"Agent state: {agent.state}")
print(f"Success: {result.success}")
print(f"Error: {result.error}")
```

3. **Inspect Stage Results**:
```python
result = orchestrator.execute(workflow_input)
for stage_result in result.output.stage_results:
    print(f"{stage_result.stage}: {stage_result.success}")
    if not stage_result.success:
        print(f"  Error: {stage_result.error}")
```

4. **Monitor Execution Time**:
```python
result = agent.execute(input_data)
print(f"Execution time: {result.execution_time_ms}ms")
```

---

## Performance Tips

### 1. Use Caching

The GEO client caches search results automatically:

```python
# First search: ~10s
result1 = search_agent.execute(search_input)

# Subsequent identical searches: <1s (cached)
result2 = search_agent.execute(search_input)
```

### 2. Limit Results

Request only what you need:

```python
# Instead of:
search_input = SearchInput(search_terms=["cancer"], max_results=1000)

# Use:
search_input = SearchInput(search_terms=["cancer"], max_results=20)
```

### 3. Use Filters

Narrow searches with filters:

```python
search_input = SearchInput(
    search_terms=["cancer"],
    max_results=50,
    organism="Homo sapiens",  # Reduces result set
    min_samples=50,            # Pre-filters low-quality
)
```

### 4. Batch Processing

Process related queries together to benefit from caching:

```python
queries = ["TP53 cancer", "TP53 mutations", "TP53 breast cancer"]
for query in queries:
    # Subsequent queries benefit from cached NLP and GEO results
    result = orchestrator.execute(OrchestratorInput(query=query))
```

### 5. Async Execution

For I/O-bound operations, use async patterns:

```python
import asyncio

async def process_queries(queries):
    tasks = [
        asyncio.create_task(process_single_query(q))
        for q in queries
    ]
    return await asyncio.gather(*tasks)
```

### 6. Monitor Performance

Track execution times:

```python
result = orchestrator.execute(workflow_input)

print(f"Total time: {result.output.total_execution_time_ms}ms")
print(f"Stages: {result.output.stages_completed}")

for stage_result in result.output.stage_results:
    print(f"{stage_result.stage}: {stage_result.execution_time_ms}ms")
```

### Performance Benchmarks

| Operation | Target | Actual (avg) |
|-----------|--------|--------------|
| Query Processing | < 10s | ~8s (first), ~0.3s (cached) |
| GEO Search | < 10s | ~7s (first), ~0.5s (cached) |
| Data Validation | < 2s | ~1.5s |
| Report Generation | < 10s | ~8s |
| Full Pipeline | < 30s | ~25s |

---

## Next Steps

- Read the [API Reference](AGENT_API_REFERENCE.md) for detailed API documentation
- Explore [Example Scripts](../examples/agent_examples.py) for working code
- Check [Phase 2 Completion Summary](PHASE_2_COMPLETION_SUMMARY.md) for project status
- Review [Testing Guide](TEST_TEMPLATES.md) for writing agent tests

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/sdodlapati3/OmicsOracle/issues
- Documentation: https://github.com/sdodlapati3/OmicsOracle/tree/main/docs

---

**OmicsOracle v2 Agent Framework** - Empowering biomedical research through intelligent multi-agent collaboration.
