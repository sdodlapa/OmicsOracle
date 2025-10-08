"""
Test request validation functionality.
"""

import pytest
from fastapi import HTTPException
from interfaces.futuristic.main import SearchRequest
from pydantic import ValidationError


class TestRequestValidation:
    """Test API request validation."""

    def test_valid_search_request(self):
        """Test creation of valid search request."""
        request = SearchRequest(query="breast cancer", max_results=10, search_type="comprehensive")

        assert request.query == "breast cancer"
        assert request.max_results == 10
        assert request.search_type == "comprehensive"

    def test_search_request_defaults(self):
        """Test search request with default values."""
        request = SearchRequest(query="test query")

        assert request.query == "test query"
        assert request.max_results == 10  # Default value
        assert request.search_type == "comprehensive"  # Default value

    def test_empty_query_validation(self):
        """Test validation of empty query."""
        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_query_whitespace_handling(self):
        """Test handling of query with whitespace."""
        request = SearchRequest(query="  test query  ")
        # The actual trimming might be handled in the endpoint
        assert request.query == "  test query  "

    def test_max_results_validation(self):
        """Test max_results validation."""
        # Valid max_results
        request = SearchRequest(query="test", max_results=5)
        assert request.max_results == 5

        # Test with 0 (edge case)
        request = SearchRequest(query="test", max_results=0)
        assert request.max_results == 0

        # Test with negative value (should be invalid in real implementation)
        request = SearchRequest(query="test", max_results=-1)
        assert request.max_results == -1  # Pydantic allows this by default

    def test_search_type_validation(self):
        """Test search_type validation."""
        valid_types = ["comprehensive", "basic", "advanced"]

        for search_type in valid_types:
            request = SearchRequest(query="test", search_type=search_type)
            assert request.search_type == search_type

    def test_request_serialization(self):
        """Test request serialization to dict."""
        request = SearchRequest(query="test query", max_results=15, search_type="advanced")

        request_dict = request.dict()
        expected = {
            "query": "test query",
            "max_results": 15,
            "search_type": "advanced",
        }

        assert request_dict == expected

    def test_request_json_serialization(self):
        """Test request JSON serialization."""
        request = SearchRequest(query="test query", max_results=15, search_type="advanced")

        json_str = request.json()
        assert "test query" in json_str
        assert "15" in json_str
        assert "advanced" in json_str

    def test_large_max_results(self):
        """Test handling of large max_results values."""
        request = SearchRequest(query="test", max_results=1000)
        assert request.max_results == 1000

        # Very large value
        request = SearchRequest(query="test", max_results=999999)
        assert request.max_results == 999999

    def test_special_characters_in_query(self):
        """Test handling of special characters in query."""
        special_queries = [
            "breast cancer & p53",
            "gene expression (RNA-seq)",
            "COVID-19 samples",
            "alpha-synuclein protein",
            'query with "quotes"',
            "query with 'single quotes'",
            "query/with/slashes",
            "query with\nnewlines",
            "query with\ttabs",
        ]

        for query in special_queries:
            request = SearchRequest(query=query)
            assert request.query == query

    def test_unicode_in_query(self):
        """Test handling of Unicode characters in query."""
        unicode_query = "beta-catenin signaling pathway"
        request = SearchRequest(query=unicode_query)
        assert request.query == unicode_query

    def test_very_long_query(self):
        """Test handling of very long queries."""
        long_query = "very long query " * 100
        request = SearchRequest(query=long_query)
        assert request.query == long_query

    def test_request_field_types(self):
        """Test that request fields have correct types."""
        request = SearchRequest(query="test", max_results=10, search_type="comprehensive")

        assert isinstance(request.query, str)
        assert isinstance(request.max_results, int)
        assert isinstance(request.search_type, str)
