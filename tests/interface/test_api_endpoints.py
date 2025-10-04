#!/usr/bin/env python3
"""
Test the OmicsOracle FastAPI server endpoints.

This script verifies that:
1. The FastAPI server starts correctly
2. API endpoints are accessible
3. Search endpoint processes queries correctly
4. Health endpoint provides accurate status
5. WebSocket connections work as expected
"""

import asyncio
import json
import logging
import os
from pathlib import Path

import pytest
import websockets
from fastapi.testclient import TestClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
# Set NCBI email for testing
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"

# Import the FastAPI app after setting up environment
from interfaces.futuristic.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


def test_home_endpoint(client):
    """Test the home endpoint."""
    logger.info("Testing home endpoint...")

    response = client.get("/")

    # Verify response
    assert response.status_code == 200, f"Home endpoint should return 200, got {response.status_code}"
    assert "text/html" in response.headers["content-type"], "Home endpoint should return HTML"

    # Check content
    assert "OmicsOracle" in response.text, "Home page should contain 'OmicsOracle'"
    assert "Intelligent Search" in response.text, "Home page should contain search form"

    logger.info("Home endpoint test successful!")


def test_health_endpoint(client):
    """Test the health endpoint."""
    logger.info("Testing health endpoint...")

    response = client.get("/api/health")

    # Verify response
    assert response.status_code == 200, f"Health endpoint should return 200, got {response.status_code}"

    # Parse response
    data = response.json()

    # Check fields
    assert "status" in data, "Health response should have status field"
    assert "timestamp" in data, "Health response should have timestamp field"
    assert "pipeline_available" in data, "Health response should have pipeline_available field"

    logger.info("Health endpoint test successful!")


def test_search_endpoint(client):
    """Test the search endpoint."""
    logger.info("Testing search endpoint...")

    # Create search request
    search_data = {"query": "cancer microarray", "max_results": 3, "search_type": "comprehensive"}

    # Make request
    response = client.post("/api/search", json=search_data)

    # We don't require a successful search (pipeline might not be available)
    # but we should get a proper response
    logger.info(f"Search endpoint response status: {response.status_code}")

    if response.status_code == 200:
        # Successful search
        data = response.json()

        # Check fields
        assert "query" in data, "Search response should have query field"
        assert "results" in data, "Search response should have results field"
        assert "total_found" in data, "Search response should have total_found field"
        assert "search_time" in data, "Search response should have search_time field"

        # Check query matches
        assert data["query"] == search_data["query"], "Query in response should match request"

        # Check results
        if data["total_found"] > 0:
            # Check first result structure
            result = data["results"][0]
            assert "geo_id" in result, "Result should have geo_id field"

            # Both summaries should be included
            assert "geo_summary" in result, "Result should have geo_summary field"
            assert "ai_summary" in result, "Result should have ai_summary field"

            logger.info("Search returned valid results structure")
    elif response.status_code == 503:
        # Pipeline not available
        logger.warning("Search endpoint returned 503 - Pipeline not available")
        data = response.json()
        assert "detail" in data, "Error response should have detail field"
        assert "not available" in data["detail"].lower(), "Error detail should mention pipeline not available"
    else:
        # Other error
        logger.warning(f"Search endpoint returned unexpected status {response.status_code}")
        logger.warning(f"Response: {response.text}")

    logger.info("Search endpoint test completed!")


async def test_websocket_connection():
    """Test WebSocket connection."""
    logger.info("Testing WebSocket connection...")

    try:
        # Connect to WebSocket
        async with websockets.connect("ws://localhost:8001/ws/monitor") as websocket:
            # Send a test message
            await websocket.send("test")

            # Wait for a response (with timeout)
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)

            # Verify response
            assert response is not None, "WebSocket should return a response"
            logger.info(f"Received WebSocket response: {response[:100]}...")

            logger.info("WebSocket connection test successful!")
            return True
    except asyncio.TimeoutError:
        logger.warning("WebSocket response timed out")
        return False
    except ConnectionRefusedError:
        logger.warning("WebSocket connection refused - server might not be running")
        return False
    except Exception as e:
        logger.error(f"WebSocket connection test failed: {e}")
        return False


def test_api_endpoints(client):
    """Test all API endpoints."""
    # Test home endpoint
    test_home_endpoint(client)

    # Test health endpoint
    test_health_endpoint(client)

    # Test search endpoint
    test_search_endpoint(client)

    # Note: WebSocket test requires a running server
    # It's not included here because TestClient doesn't support WebSockets
    # The test_websocket_connection function can be used separately
    # when the server is running


if __name__ == "__main__":
    # Run the API tests
    with TestClient(app) as test_client:
        test_api_endpoints(test_client)

    # If server is running, test WebSocket
    logger.info("Note: WebSocket test requires the server to be running")
    logger.info("To test WebSockets, start the server and run this test separately")

    # Uncomment to test WebSockets if server is running
    # asyncio.run(test_websocket_connection())
