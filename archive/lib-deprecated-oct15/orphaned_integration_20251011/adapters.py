"""
Response adapter - maps backend responses to integration layer models
"""
from typing import Any, Dict

from omics_oracle_v2.integration.models import (Publication, SearchMetadata,
                                                SearchResponse)


def adapt_search_response(backend_response: Dict[str, Any]) -> SearchResponse:
    """
    Adapt backend search response to integration layer SearchResponse model.

    Backend format:
    {
        "success": true,
        "execution_time_ms": 12746.02,
        "timestamp": "2025-10-08T06:41:59.302005Z",
        "total_found": 5,
        "datasets": [{
            "geo_id": "GSE292511",
            "title": "...",
            "summary": "...",
            "organism": "",
            "sample_count": 16,
            "platform": "GPL21290",
            "relevance_score": 0.4,
            "match_reasons": [...]
        }],
        "search_terms_used": ["CRISPR"],
        "filters_applied": {}
    }

    Integration layer format:
    SearchResponse(
        results=[Publication(...)],
        metadata=SearchMetadata(
            total_results=5,
            query="CRISPR",
            ...
        )
    )
    """
    # Extract datasets (GEO database results)
    datasets = backend_response.get("datasets", [])

    # Convert to Publication objects
    publications = []
    for dataset in datasets:
        pub = Publication(
            id=dataset.get("geo_id", ""),
            title=dataset.get("title", ""),
            abstract=dataset.get("summary", ""),
            authors=[],  # GEO datasets don't have author info in this response
            year=None,  # Not in response
            journal="GEO Database",  # Source is GEO
            doi=None,
            pmid=None,
            citations=None,
            # Custom fields from GEO
            metadata={
                "geo_id": dataset.get("geo_id"),
                "organism": dataset.get("organism"),
                "sample_count": dataset.get("sample_count"),
                "platform": dataset.get("platform"),
                "relevance_score": dataset.get("relevance_score"),
                "match_reasons": dataset.get("match_reasons", []),
            },
        )
        publications.append(pub)

    # Build metadata
    search_terms = backend_response.get("search_terms_used", [])
    query_string = " ".join(search_terms) if search_terms else ""

    metadata = SearchMetadata(
        total_results=backend_response.get("total_found", 0),
        page=1,
        per_page=len(publications),
        query=query_string,
        databases=["GEO"],  # This endpoint searches GEO
        execution_time_ms=backend_response.get("execution_time_ms"),
        timestamp=backend_response.get("timestamp"),
    )

    return SearchResponse(results=publications, metadata=metadata)


def adapt_analysis_response(backend_response: Dict[str, Any]):
    """Adapt backend analysis response (TODO)"""
    # To be implemented when we test AnalysisClient
    return backend_response


def adapt_recommendation_response(backend_response: Dict[str, Any]):
    """Adapt backend recommendation response (TODO)"""
    # To be implemented when we test MLClient
    return backend_response
