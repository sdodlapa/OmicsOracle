#!/usr/bin/env python3
"""
Architecture Refactoring Implementation Guide

This script provides concrete examples and templates for implementing
the recommended architectural changes for OmicsOracle.
"""

from pathlib import Path
from typing import Dict, List


def create_clean_architecture_skeleton():
    """Create the new directory structure for clean architecture."""

    directories = [
        # Domain layer
        "src/omics_oracle_v2/domain/entities",
        "src/omics_oracle_v2/domain/services",
        "src/omics_oracle_v2/domain/repositories",
        "src/omics_oracle_v2/domain/events",
        # Application layer
        "src/omics_oracle_v2/application/use_cases",
        "src/omics_oracle_v2/application/dto",
        "src/omics_oracle_v2/application/interfaces",
        "src/omics_oracle_v2/application/handlers",
        # Infrastructure layer
        "src/omics_oracle_v2/infrastructure/persistence",
        "src/omics_oracle_v2/infrastructure/external/ncbi",
        "src/omics_oracle_v2/infrastructure/external/openai",
        "src/omics_oracle_v2/infrastructure/monitoring",
        "src/omics_oracle_v2/infrastructure/config",
        "src/omics_oracle_v2/infrastructure/cache",
        # Presentation layer
        "src/omics_oracle_v2/presentation/api/routes",
        "src/omics_oracle_v2/presentation/api/middleware",
        "src/omics_oracle_v2/presentation/web/routes",
        "src/omics_oracle_v2/presentation/web/static",
        "src/omics_oracle_v2/presentation/cli",
        # Shared utilities
        "src/omics_oracle_v2/shared/exceptions",
        "src/omics_oracle_v2/shared/logging",
        "src/omics_oracle_v2/shared/types",
        "src/omics_oracle_v2/shared/utils",
        # Tests
        "tests/unit/domain",
        "tests/unit/application",
        "tests/unit/infrastructure",
        "tests/unit/presentation",
        "tests/integration",
        "tests/e2e",
    ]

    return directories


# Domain Entities Example
domain_entities_example = '''
"""
Domain entities for OmicsOracle
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class DatasetType(Enum):
    GEO_SERIES = "geo_series"
    GEO_SAMPLE = "geo_sample"
    SRA_STUDY = "sra_study"


class SummaryType(Enum):
    AUTO_GENERATED = "auto_generated"
    MANUAL = "manual"
    AI_ENHANCED = "ai_enhanced"


@dataclass(frozen=True)
class DatasetId:
    """Value object for dataset identifier."""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Dataset ID cannot be empty")


@dataclass(frozen=True)
class Query:
    """Value object representing a search query."""
    text: str
    max_results: int = 10
    filters: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.text or not self.text.strip():
            raise ValueError("Query text cannot be empty")
        if self.max_results <= 0:
            raise ValueError("Max results must be positive")


@dataclass
class Dataset:
    """Core dataset entity."""
    id: DatasetId
    title: str
    type: DatasetType
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    @property
    def organism(self) -> Optional[str]:
        return self.metadata.get("organism")

    @property
    def sample_count(self) -> Optional[int]:
        return self.metadata.get("sample_count")


@dataclass
class Summary:
    """Summary entity."""
    content: str
    type: SummaryType
    dataset_id: DatasetId
    created_at: datetime
    confidence_score: Optional[float] = None

    def is_high_confidence(self) -> bool:
        return self.confidence_score is not None and self.confidence_score > 0.8


@dataclass
class SearchResult:
    """Aggregate for search results."""
    query: Query
    datasets: List[Dataset]
    summaries: Dict[DatasetId, Summary]
    total_found: int
    execution_time: float

    @property
    def result_count(self) -> int:
        return len(self.datasets)

    def get_summary_for_dataset(self, dataset_id: DatasetId) -> Optional[Summary]:
        return self.summaries.get(dataset_id)
'''

# Domain Services Example
domain_services_example = '''
"""
Domain services interfaces
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Dataset, DatasetId, Query, Summary, SearchResult


class SearchService(ABC):
    """Domain service for dataset searching."""

    @abstractmethod
    async def search_datasets(self, query: Query) -> List[Dataset]:
        """Search for datasets matching the query."""
        pass

    @abstractmethod
    async def get_dataset_by_id(self, dataset_id: DatasetId) -> Optional[Dataset]:
        """Retrieve a specific dataset by ID."""
        pass


class SummarizationService(ABC):
    """Domain service for content summarization."""

    @abstractmethod
    async def generate_summary(self, dataset: Dataset) -> Summary:
        """Generate an AI summary for a dataset."""
        pass

    @abstractmethod
    async def enhance_summary(self, existing_summary: Summary, context: str) -> Summary:
        """Enhance an existing summary with additional context."""
        pass


class QueryAnalysisService(ABC):
    """Domain service for query analysis and enhancement."""

    @abstractmethod
    async def analyze_intent(self, query: Query) -> Dict[str, Any]:
        """Analyze the intent behind a search query."""
        pass

    @abstractmethod
    async def suggest_refinements(self, query: Query, results: SearchResult) -> List[str]:
        """Suggest query refinements based on results."""
        pass
'''

# Use Cases Example
use_cases_example = '''
"""
Application use cases
"""

from typing import Dict, Any, List
from ..domain.entities import Query, SearchResult, Dataset, Summary, DatasetId
from ..domain.services import SearchService, SummarizationService, QueryAnalysisService


class SearchDatasetsUseCase:
    """Use case for searching datasets with AI summarization."""

    def __init__(
        self,
        search_service: SearchService,
        summarization_service: SummarizationService,
        query_analysis_service: QueryAnalysisService
    ):
        self._search_service = search_service
        self._summarization_service = summarization_service
        self._query_analysis_service = query_analysis_service

    async def execute(self, query: Query) -> SearchResult:
        """Execute the search datasets use case."""
        import time
        start_time = time.time()

        # Analyze query intent
        intent_analysis = await self._query_analysis_service.analyze_intent(query)

        # Search for datasets
        datasets = await self._search_service.search_datasets(query)

        # Generate summaries for each dataset
        summaries = {}
        for dataset in datasets:
            summary = await self._summarization_service.generate_summary(dataset)
            summaries[dataset.id] = summary

        execution_time = time.time() - start_time

        return SearchResult(
            query=query,
            datasets=datasets,
            summaries=summaries,
            total_found=len(datasets),
            execution_time=execution_time
        )


class GetDatasetDetailsUseCase:
    """Use case for retrieving detailed dataset information."""

    def __init__(
        self,
        search_service: SearchService,
        summarization_service: SummarizationService
    ):
        self._search_service = search_service
        self._summarization_service = summarization_service

    async def execute(self, dataset_id: DatasetId) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific dataset."""
        dataset = await self._search_service.get_dataset_by_id(dataset_id)
        if not dataset:
            return None

        summary = await self._summarization_service.generate_summary(dataset)

        return {
            "dataset": dataset,
            "summary": summary,
            "metadata": dataset.metadata
        }
'''

# Infrastructure Implementation Example
infrastructure_example = '''
"""
Infrastructure implementations
"""

import aiohttp
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.entities import Dataset, DatasetId, Query, Summary, DatasetType, SummaryType
from ..domain.services import SearchService, SummarizationService
from ..shared.exceptions import ExternalServiceError


class NCBIGEOSearchService(SearchService):
    """NCBI GEO implementation of search service."""

    def __init__(self, base_url: str, email: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.email = email
        self.api_key = api_key

    async def search_datasets(self, query: Query) -> List[Dataset]:
        """Search NCBI GEO for datasets."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "db": "gds",
                    "term": query.text,
                    "retmax": query.max_results,
                    "email": self.email,
                    "tool": "omics_oracle"
                }

                if self.api_key:
                    params["api_key"] = self.api_key

                url = f"{self.base_url}/esearch.fcgi"
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.text()
                    # Parse XML response and create Dataset objects
                    return self._parse_search_results(data)

        except Exception as e:
            raise ExternalServiceError(f"NCBI search failed: {e}")

    async def get_dataset_by_id(self, dataset_id: DatasetId) -> Optional[Dataset]:
        """Retrieve dataset by ID from NCBI."""
        # Implementation for fetching specific dataset
        pass

    def _parse_search_results(self, xml_data: str) -> List[Dataset]:
        """Parse XML search results into Dataset entities."""
        # Implementation for parsing XML
        datasets = []
        # ... parsing logic ...
        return datasets


class OpenAISummarizationService(SummarizationService):
    """OpenAI implementation of summarization service."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    async def generate_summary(self, dataset: Dataset) -> Summary:
        """Generate AI summary using OpenAI."""
        try:
            # Prepare context from dataset
            context = self._prepare_context(dataset)

            # Call OpenAI API
            summary_text = await self._call_openai_api(context)

            return Summary(
                content=summary_text,
                type=SummaryType.AI_ENHANCED,
                dataset_id=dataset.id,
                created_at=datetime.now(),
                confidence_score=0.85  # Could be calculated based on response
            )

        except Exception as e:
            raise ExternalServiceError(f"OpenAI summarization failed: {e}")

    async def enhance_summary(self, existing_summary: Summary, context: str) -> Summary:
        """Enhance existing summary with additional context."""
        # Implementation for summary enhancement
        pass

    def _prepare_context(self, dataset: Dataset) -> str:
        """Prepare context for summarization."""
        return f"Title: {dataset.title}\\nMetadata: {dataset.metadata}"

    async def _call_openai_api(self, context: str) -> str:
        """Call OpenAI API for summarization."""
        # Implementation for OpenAI API call
        return "Generated summary based on context"
'''

# Dependency Injection Container Example
di_container_example = '''
"""
Dependency injection container configuration
"""

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide

from .infrastructure.external.ncbi import NCBIGEOSearchService
from .infrastructure.external.openai import OpenAISummarizationService
from .infrastructure.external.nlp import NLPQueryAnalysisService
from .application.use_cases import SearchDatasetsUseCase, GetDatasetDetailsUseCase
from .infrastructure.config import Settings


class ApplicationContainer(containers.DeclarativeContainer):
    """Dependency injection container for the application."""

    # Configuration
    config = providers.Configuration()

    # Infrastructure services
    search_service = providers.Singleton(
        NCBIGEOSearchService,
        base_url=config.ncbi.base_url,
        email=config.ncbi.email,
        api_key=config.ncbi.api_key
    )

    summarization_service = providers.Singleton(
        OpenAISummarizationService,
        api_key=config.openai.api_key,
        model=config.openai.model
    )

    query_analysis_service = providers.Singleton(
        NLPQueryAnalysisService,
        model_path=config.nlp.model_path
    )

    # Use cases
    search_datasets_use_case = providers.Factory(
        SearchDatasetsUseCase,
        search_service=search_service,
        summarization_service=summarization_service,
        query_analysis_service=query_analysis_service
    )

    get_dataset_details_use_case = providers.Factory(
        GetDatasetDetailsUseCase,
        search_service=search_service,
        summarization_service=summarization_service
    )


# Wiring configuration
def create_container() -> ApplicationContainer:
    """Create and configure the dependency injection container."""
    container = ApplicationContainer()

    # Load configuration from environment
    settings = Settings()
    container.config.from_pydantic(settings)

    return container


# Usage in FastAPI
from fastapi import FastAPI, Depends

def create_app() -> FastAPI:
    """Create FastAPI application with dependency injection."""
    app = FastAPI(title="OmicsOracle API")
    container = create_container()

    # Wire the container
    container.wire(modules=["presentation.api.routes"])

    # Add container to app state
    app.container = container

    return app


# Example route with dependency injection
async def search_datasets(
    query: str,
    max_results: int = 10,
    use_case: SearchDatasetsUseCase = Depends(Provide[ApplicationContainer.search_datasets_use_case])
):
    """Search datasets endpoint."""
    query_obj = Query(text=query, max_results=max_results)
    result = await use_case.execute(query_obj)

    return {
        "query": result.query.text,
        "total_found": result.total_found,
        "execution_time": result.execution_time,
        "datasets": [
            {
                "id": dataset.id.value,
                "title": dataset.title,
                "type": dataset.type.value,
                "summary": result.get_summary_for_dataset(dataset.id).content
            }
            for dataset in result.datasets
        ]
    }
'''


def main():
    """Generate the refactoring implementation guide."""

    examples = {
        "1_domain_entities.py": domain_entities_example,
        "2_domain_services.py": domain_services_example,
        "3_use_cases.py": use_cases_example,
        "4_infrastructure.py": infrastructure_example,
        "5_dependency_injection.py": di_container_example,
    }

    # Create output directory
    output_dir = Path("docs/refactoring_examples")
    output_dir.mkdir(exist_ok=True)

    # Write example files
    for filename, content in examples.items():
        file_path = output_dir / filename
        with open(file_path, "w") as f:
            f.write(content.strip() + "\\n")
        print(f"Created: {file_path}")

    # Generate directory structure
    directories = create_clean_architecture_skeleton()
    structure_file = output_dir / "directory_structure.txt"
    with open(structure_file, "w") as f:
        f.write("# Proposed Directory Structure\\n\\n")
        for directory in directories:
            f.write(f"{directory}/\\n")

    print(f"\\nRefactoring examples created in: {output_dir}")
    print("\\nNext steps:")
    print("1. Review the example implementations")
    print("2. Create the new directory structure")
    print("3. Start implementing domain entities")
    print("4. Set up dependency injection")
    print("5. Gradually migrate existing code")


if __name__ == "__main__":
    main()
