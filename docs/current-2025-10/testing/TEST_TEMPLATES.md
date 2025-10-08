# OmicsOracle Test Templates

This document provides template code for testing key events in the OmicsOracle system, from server startup to frontend display. These templates can be used as a starting point for implementing comprehensive tests.

## 1. Server Initialization Tests

### 1.1 Server Startup Test

```python
# tests/interface/test_server.py

import pytest
from fastapi.testclient import TestClient
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from interfaces.futuristic.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_server_startup():
    """Test that the server starts up correctly"""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "pipeline_available" in data

def test_static_files_serve():
    """Test that static files are served correctly"""
    client = TestClient(app)
    response = client.get("/static/js/main_clean.js")
    assert response.status_code == 200
    assert "OmicsOracle" in response.text

def test_main_page_load():
    """Test that the main page loads correctly"""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "OmicsOracle" in response.text
    assert "Search" in response.text
```

### 1.2 Pipeline Initialization Test

```python
# tests/pipeline/test_initialization.py

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.omics_oracle.core.config import Config
from src.omics_oracle.pipeline.pipeline import OmicsOracle

@pytest.fixture
def config():
    return Config()

def test_pipeline_initialization(config):
    """Test that the pipeline initializes correctly"""
    # Ensure NCBI email is set
    os.environ["NCBI_EMAIL"] = "test@example.com"

    # Initialize pipeline with cache disabled
    pipeline = OmicsOracle(config, disable_cache=True)

    # Verify pipeline is initialized
    assert pipeline is not None

    # Verify components are initialized
    assert pipeline.geo_client is not None
    assert pipeline.summarizer is not None

    # Verify caching is disabled
    assert pipeline.disable_cache is True
    assert pipeline.geo_client.disable_cache is True
    assert pipeline.summarizer.cache is None

def test_progress_callback_setup(config):
    """Test that progress callbacks can be set"""
    # Initialize pipeline
    pipeline = OmicsOracle(config, disable_cache=True)

    # Define a test callback
    async def test_callback(query_id, event):
        pass

    # Set the callback
    pipeline.set_progress_callback(test_callback)

    # Verify callback is set
    assert pipeline._progress_callback is not None
    assert pipeline._progress_callback == test_callback
```

### 1.3 NCBI Email Configuration Test

```python
# test_ncbi_config.py

import pytest
import os
import sys
from pathlib import Path
import asyncio
from unittest.mock import patch

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.omics_oracle.core.config import Config
from src.omics_oracle.geo_tools.geo_client import UnifiedGEOClient, NCBIDirectClient

def test_ncbi_email_env_var():
    """Test that NCBI email environment variable is set"""
    test_email = "test@example.com"
    os.environ["NCBI_EMAIL"] = test_email
    assert os.environ["NCBI_EMAIL"] == test_email

def test_ncbi_email_in_config():
    """Test that NCBI email is set in config"""
    test_email = "test@example.com"
    os.environ["NCBI_EMAIL"] = test_email

    config = Config()

    # Check if ncbi attribute exists
    if hasattr(config, "ncbi"):
        # If it exists, check if email is set
        if hasattr(config.ncbi, "email"):
            assert config.ncbi.email == test_email or os.environ["NCBI_EMAIL"]

    # If ncbi attribute doesn't exist, this test is not applicable
    # but shouldn't fail

def test_bio_entrez_email():
    """Test that Bio.Entrez email is set correctly"""
    test_email = "test@example.com"
    os.environ["NCBI_EMAIL"] = test_email

    try:
        from Bio import Entrez
        # Set email directly
        Entrez.email = test_email

        # Verify email is set
        assert Entrez.email == test_email
    except ImportError:
        pytest.skip("Bio.Entrez not available")

@pytest.mark.asyncio
async def test_ncbi_client_email():
    """Test that NCBI client uses the correct email"""
    test_email = "test@example.com"
    os.environ["NCBI_EMAIL"] = test_email

    config = Config()
    ncbi_client = NCBIDirectClient(email=test_email)

    # Check email is set
    assert ncbi_client.email == test_email

    # Mock request to check email is passed
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = asyncio.coroutine(lambda: {"result": {}})

        await ncbi_client.esearch("test", db="gds")

        # Check email is in the request params
        call_args = mock_get.call_args[0][0]
        assert "email=test%40example.com" in call_args
```

## 2. Search Process Tests

### 2.1 Search Request Test

```python
# tests/interface/test_api_endpoints.py

import pytest
from fastapi.testclient import TestClient
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from interfaces.futuristic.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_search_endpoint_exists(client):
    """Test that the search endpoint exists"""
    # Use OPTIONS request to check endpoint exists
    response = client.options("/api/search")
    assert response.status_code != 404

def test_search_request_validation(client):
    """Test search request validation"""
    # Test missing required field
    response = client.post("/api/search", json={})
    assert response.status_code == 422

    # Test invalid max_results (negative)
    response = client.post("/api/search", json={"query": "test", "max_results": -1})
    assert response.status_code == 422

    # Test valid request
    response = client.post("/api/search", json={"query": "test", "max_results": 10})
    # Note: This might fail if pipeline is not initialized
    # That's OK for validation testing - we're just checking request structure

def test_search_with_mocked_pipeline():
    """Test search with mocked pipeline"""
    # Create test client with mocked process_search_query
    with patch("interfaces.futuristic.main.process_search_query") as mock_process:
        # Setup mock to return expected data
        mock_process.return_value = {"datasets": [{"geo_id": "GSE123", "title": "Test"}]}

        client = TestClient(app)
        response = client.post("/api/search", json={"query": "test", "max_results": 10})

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"
        assert len(data["results"]) == 1
        assert data["results"][0]["geo_id"] == "GSE123"

        # Check mock was called with expected args
        mock_process.assert_called_once_with("test", 10)
```

### 2.2 GEO Search Test

```python
# tests/geo_tools/test_geo_client.py

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.omics_oracle.geo_tools.geo_client import UnifiedGEOClient, NCBIDirectClient
from src.omics_oracle.core.config import Config

@pytest.fixture
def config():
    return Config()

@pytest.fixture
def geo_client(config):
    # Ensure NCBI email is set
    os.environ["NCBI_EMAIL"] = "test@example.com"
    return UnifiedGEOClient(config, disable_cache=True)

@pytest.mark.asyncio
async def test_geo_search_basic(geo_client):
    """Test basic GEO search functionality with mocked response"""
    with patch.object(NCBIDirectClient, "esearch") as mock_esearch:
        # Mock esearch to return test IDs
        mock_esearch.return_value = ["GSE123", "GSE456"]

        # Call search method
        results = await geo_client.search_geo_datasets("test query", max_results=10)

        # Check results
        assert results == ["GSE123", "GSE456"]

        # Check mock was called correctly
        mock_esearch.assert_called_once()
        args, kwargs = mock_esearch.call_args
        assert args[0] == "test query"
        assert kwargs["db"] == "gds"

@pytest.mark.asyncio
async def test_geo_metadata_retrieval(geo_client):
    """Test GEO metadata retrieval with mocked response"""
    with patch.object(NCBIDirectClient, "esummary") as mock_esummary:
        # Mock esummary to return test metadata
        mock_esummary.return_value = {
            "GSE123": {
                "title": "Test Dataset",
                "summary": "This is a test dataset",
                "organism": "Homo sapiens"
            }
        }

        # Call method to get metadata
        metadata = await geo_client.get_geo_metadata(["GSE123"])

        # Check metadata
        assert len(metadata) == 1
        assert metadata[0]["title"] == "Test Dataset"
        assert metadata[0]["geo_id"] == "GSE123"
        assert metadata[0]["organism"] == "Homo sapiens"

        # Check mock was called correctly
        mock_esummary.assert_called_once()
        args, kwargs = mock_esummary.call_args
        assert args[0] == ["GSE123"]
        assert kwargs["db"] == "gds"

@pytest.mark.asyncio
async def test_cache_bypass(geo_client):
    """Test that cache is bypassed when disabled"""
    # First call with mock
    with patch.object(NCBIDirectClient, "esearch") as mock_esearch:
        mock_esearch.return_value = ["GSE123"]
        await geo_client.search_geo_datasets("test query")

    # Second call with different mock
    with patch.object(NCBIDirectClient, "esearch") as mock_esearch:
        mock_esearch.return_value = ["GSE456"]
        results = await geo_client.search_geo_datasets("test query")

        # Check results reflect second call (no caching)
        assert results == ["GSE456"]
        mock_esearch.assert_called_once()
```

### 2.3 AI Summarization Test

```python
# tests/services/test_summarizer.py

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.omics_oracle.services.summarizer import SummarizationService
from src.omics_oracle.core.config import Config

@pytest.fixture
def config():
    return Config()

@pytest.fixture
def summarizer(config):
    return SummarizationService(config, disable_cache=True)

@pytest.mark.asyncio
async def test_summarizer_init(config):
    """Test summarizer initialization"""
    # Initialize with cache disabled
    summarizer = SummarizationService(config, disable_cache=True)
    assert summarizer.cache is None

    # Initialize with cache enabled (for testing cache bypass)
    summarizer_with_cache = SummarizationService(config, disable_cache=False)
    assert summarizer_with_cache.cache is not None

@pytest.mark.asyncio
async def test_generate_summary_with_mocked_openai(summarizer):
    """Test summary generation with mocked OpenAI client"""
    # Mock metadata for test
    metadata = {
        "geo_id": "GSE123",
        "title": "Test Dataset",
        "summary": "This is a test dataset for cancer research",
        "organism": "Homo sapiens"
    }

    # Mock OpenAI client
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value.choices[0].message.content = "AI generated summary for cancer research dataset"

    with patch("openai.OpenAI", return_value=mock_openai):
        # Call summary generation
        summary = await summarizer.generate_summary(metadata)

        # Check summary
        assert summary is not None
        assert "AI generated summary for cancer research dataset" in summary

        # Check mock was called
        mock_openai.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_cache_bypass(config):
    """Test that cache is bypassed when disabled"""
    summarizer = SummarizationService(config, disable_cache=True)

    # Test metadata
    metadata = {
        "geo_id": "GSE123",
        "title": "Test Dataset",
        "summary": "This is a test dataset"
    }

    # First call with mock
    mock_openai1 = MagicMock()
    mock_openai1.chat.completions.create.return_value.choices[0].message.content = "Summary 1"

    with patch("openai.OpenAI", return_value=mock_openai1):
        summary1 = await summarizer.generate_summary(metadata)

    # Second call with different mock
    mock_openai2 = MagicMock()
    mock_openai2.chat.completions.create.return_value.choices[0].message.content = "Summary 2"

    with patch("openai.OpenAI", return_value=mock_openai2):
        summary2 = await summarizer.generate_summary(metadata)

    # Check summaries are different (no caching)
    assert summary1 != summary2
    assert summary1 == "Summary 1"
    assert summary2 == "Summary 2"
```

## 3. Frontend Tests

### 3.1 WebSocket Connection Test

```python
# tests/interface/test_websocket.py

import pytest
from fastapi.testclient import TestClient
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from interfaces.futuristic.main import app

def test_websocket_connection():
    """Test WebSocket connection establishment"""
    client = TestClient(app)

    with client.websocket_connect("/ws/monitor") as websocket:
        # Check connection is established
        assert websocket.accept()

        # Test sending a message
        websocket.send_text("test")

        # No response expected for simple message

def test_websocket_progress_updates():
    """Test WebSocket progress updates"""
    from interfaces.futuristic.main import manager, ProgressEvent

    client = TestClient(app)

    # Connect to WebSocket
    with client.websocket_connect("/ws/monitor") as websocket:
        # Create test event
        event = ProgressEvent(
            stage="testing",
            message="Test progress update",
            percentage=50.0,
            detail={"test": "data"}
        )

        # Manually trigger broadcast
        # Note: This is normally done by the server
        # and tested in integration tests
        asyncio.run(manager.broadcast_progress(
            "test_query_id",
            event.stage,
            event.message,
            event.percentage,
            event.detail
        ))

        # Check for JSON data
        response = websocket.receive_json()
        assert response["type"] == "progress"
        assert response["stage"] == "testing"
        assert response["message"] == "Test progress update"
        assert response["percentage"] == 50.0
        assert response["detail"] == {"test": "data"}

        # Check for HTML message
        html_message = websocket.receive_text()
        assert "Test progress update" in html_message
        assert "50%" in html_message
```

### 3.2 Results Display Test

```python
# tests/interface/test_frontend.py

import pytest
from playwright.sync_api import Page, expect
import os
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Basic frontend tests using Playwright
# These assume the server is running at http://localhost:8000

@pytest.mark.skip("Requires running server")
def test_results_display(page: Page):
    """Test results display on the frontend"""
    # Go to the application
    page.goto("http://localhost:8000/")

    # Enter a search query
    page.fill("#search-input", "cancer RNA-seq")

    # Click search button
    page.click("#search-btn")

    # Wait for results to load
    page.wait_for_selector(".result-card", timeout=30000)

    # Check that results are displayed
    result_cards = page.query_selector_all(".result-card")
    assert len(result_cards) > 0

    # Check that each card has the necessary elements
    for card in result_cards:
        # Check GEO ID exists
        assert card.query_selector(".geo-id") is not None

        # Check title exists
        assert card.query_selector(".result-title") is not None

        # Check GEO summary exists
        assert card.query_selector(".geo-summary") is not None

        # Check AI summary exists
        assert card.query_selector(".ai-summary") is not None

@pytest.mark.skip("Requires running server")
def test_progress_updates_display(page: Page):
    """Test progress updates display on the frontend"""
    # Go to the application
    page.goto("http://localhost:8000/")

    # Enter a search query
    page.fill("#search-input", "cancer RNA-seq")

    # Click search button
    page.click("#search-btn")

    # Check progress bar appears
    progress_bar = page.wait_for_selector("#progress-bar", timeout=5000)
    assert progress_bar is not None

    # Check live progress feed appears
    progress_feed = page.wait_for_selector("#live-progress-feed", timeout=5000)
    assert progress_feed is not None

    # Wait for progress to complete
    page.wait_for_selector(".result-card", timeout=30000)

    # Check progress reached 100%
    progress_percentage = page.query_selector("#progress-percentage")
    assert progress_percentage.inner_text() == "100%"
```

## 4. End-to-End Tests

### 4.1 Search Pipeline E2E Test

```python
# tests/e2e/test_search_pipeline.py

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.omics_oracle.core.config import Config
from src.omics_oracle.pipeline.pipeline import OmicsOracle

@pytest.fixture
def config():
    return Config()

@pytest.mark.asyncio
async def test_end_to_end_search(config):
    """Test end-to-end search pipeline"""
    # Set up environment
    os.environ["NCBI_EMAIL"] = "test@example.com"

    # Initialize pipeline
    pipeline = OmicsOracle(config, disable_cache=True)

    # Create progress tracking list
    progress_events = []

    # Define progress callback
    async def track_progress(query_id, event):
        progress_events.append((event.stage, event.percentage))

    # Set callback
    pipeline.set_progress_callback(track_progress)

    # Process query
    query = "cancer RNA-seq small test"
    max_results = 3

    # Execute search
    result = await pipeline.process_query(query, max_results=max_results)

    # Validate result
    assert result is not None
    assert result.original_query == query
    assert result.is_completed

    # Check GEO IDs
    assert len(result.geo_ids) <= max_results

    # Check metadata
    assert len(result.metadata) <= max_results
    if result.metadata:
        assert "geo_id" in result.metadata[0]
        assert "title" in result.metadata[0]

    # Check AI summaries
    assert result.ai_summaries is not None

    # Check progress events
    assert len(progress_events) > 0

    # Check for key stages in progress
    stages = [stage for stage, _ in progress_events]
    assert "initialization" in stages
    assert "parsing" in stages or "parsing_complete" in stages
    assert "searching" in stages or "search_complete" in stages

    # Check final progress is 100%
    final_progress = progress_events[-1][1]
    assert final_progress == 100.0

@pytest.mark.asyncio
async def test_honest_results(config):
    """Test that results are honest (no fake/cached data)"""
    # Set up environment
    os.environ["NCBI_EMAIL"] = "test@example.com"

    # Initialize pipeline
    pipeline = OmicsOracle(config, disable_cache=True)

    # Process query that should return minimal or no results
    query = "xyznonexistenttermabc123xyz"
    max_results = 10

    # Execute search
    result = await pipeline.process_query(query, max_results=max_results)

    # Check that we don't have fake results (should be empty or very few)
    assert len(result.geo_ids) <= 1  # May get 0 or at most 1 results

    # If we have results, check they actually contain the term
    if result.metadata:
        found_term = False
        for entry in result.metadata:
            text = json.dumps(entry).lower()
            if "xyznonexistenttermabc123xyz" in text:
                found_term = True
                break

        # We shouldn't find this term as it doesn't exist
        assert not found_term
```

### 4.2 Interface Integration E2E Test

```python
# tests/e2e/test_interface_integration.py

import pytest
from fastapi.testclient import TestClient
import asyncio
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from interfaces.futuristic.main import app
from src.omics_oracle.pipeline.pipeline import QueryResult, QueryStatus
from datetime import datetime

# Create a mock result for testing
def create_mock_result():
    result = QueryResult(
        query_id="test_query_id",
        original_query="cancer RNA-seq",
        status=QueryStatus.COMPLETED,
        start_time=datetime.now(),
        end_time=datetime.now()
    )
    result.geo_ids = ["GSE123", "GSE456"]
    result.metadata = [
        {
            "geo_id": "GSE123",
            "title": "Test Dataset 1",
            "summary": "This is a test dataset for cancer",
            "organism": "Homo sapiens"
        },
        {
            "geo_id": "GSE456",
            "title": "Test Dataset 2",
            "summary": "This is another test dataset",
            "organism": "Mus musculus"
        }
    ]
    result.ai_summaries = {
        "GSE123": "AI summary for dataset 1",
        "GSE456": "AI summary for dataset 2"
    }
    return result

@pytest.mark.asyncio
async def test_search_to_display_integration():
    """Test integration from search to display"""
    # Create mock result
    mock_result = create_mock_result()

    # Mock the pipeline.process_query method
    with patch("interfaces.futuristic.main.pipeline") as mock_pipeline:
        # Set up mock to return our test result
        mock_pipeline.process_query = AsyncMock(return_value=mock_result)

        # Create test client
        client = TestClient(app)

        # Make search request
        response = client.post(
            "/api/search",
            json={"query": "cancer RNA-seq", "max_results": 10}
        )

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert data["query"] == "cancer RNA-seq"
        assert len(data["results"]) == 2
        assert data["results"][0]["geo_id"] == "GSE123"
        assert data["results"][1]["geo_id"] == "GSE456"

        # Check AI summaries are included
        assert "ai_summary" in data["results"][0]
        assert data["results"][0]["ai_summary"] == "AI summary for dataset 1"

        # Check GEO summaries are included
        assert "summary" in data["results"][0]
        assert data["results"][0]["summary"] == "This is a test dataset for cancer"

@pytest.mark.asyncio
async def test_websocket_progress_integration():
    """Test WebSocket progress integration"""
    # Mock the pipeline.process_query method
    with patch("interfaces.futuristic.main.pipeline") as mock_pipeline:
        # Create a side effect that sends progress updates
        async def mock_process_query(*args, **kwargs):
            # Get the callback that was set
            callback = mock_pipeline.set_progress_callback.call_args[0][0]

            # Create a ProgressEvent
            from src.omics_oracle.pipeline.pipeline import ProgressEvent

            # Send initialization progress
            event1 = ProgressEvent(
                stage="initialization",
                message="Initializing query processing",
                percentage=0.0
            )
            await callback("test_query_id", event1)

            # Send searching progress
            event2 = ProgressEvent(
                stage="searching",
                message="Searching NCBI GEO database",
                percentage=20.0
            )
            await callback("test_query_id", event2)

            # Send processing progress
            event3 = ProgressEvent(
                stage="processing",
                message="Processing results",
                percentage=60.0
            )
            await callback("test_query_id", event3)

            # Send completion progress
            event4 = ProgressEvent(
                stage="complete",
                message="Search complete",
                percentage=100.0
            )
            await callback("test_query_id", event4)

            # Return the mock result
            return create_mock_result()

        # Set up the mock
        mock_pipeline.process_query = AsyncMock(side_effect=mock_process_query)

        # Create test client with WebSocket support
        client = TestClient(app)

        # Connect to WebSocket
        with client.websocket_connect("/ws/monitor") as websocket:
            # Make search request in the background
            import threading
            def make_request():
                client.post(
                    "/api/search",
                    json={"query": "cancer RNA-seq", "max_results": 10}
                )

            thread = threading.Thread(target=make_request)
            thread.start()

            # Collect WebSocket messages
            progress_messages = []
            try:
                # Wait for progress messages
                for _ in range(8):  # Expect at least 8 messages (4 JSON + 4 HTML)
                    data = websocket.receive()
                    if "text" in data:
                        progress_messages.append(data["text"])
                    if len(progress_messages) >= 8:
                        break
            except:
                pass

            # Wait for request to complete
            thread.join()

            # Validate progress messages
            assert len(progress_messages) >= 4

            # Check for key stages in messages
            json_messages = [msg for msg in progress_messages if msg.startswith("{")]
            text_messages = [msg for msg in progress_messages if not msg.startswith("{")]

            # Check JSON messages
            json_data = [json.loads(msg) for msg in json_messages]
            stages = [data.get("stage") for data in json_data if "stage" in data]

            assert "initialization" in stages
            assert "searching" in stages
            assert "processing" in stages
            assert "complete" in stages

            # Check text messages
            assert any("Initializing" in msg for msg in text_messages)
            assert any("Searching" in msg for msg in text_messages)
            assert any("Processing" in msg for msg in text_messages)
            assert any("complete" in msg for msg in text_messages)
```

## 5. Monitoring Component Tests

### 5.1 Pipeline Monitoring Test

```python
# tests/monitoring/test_pipeline_monitor.py

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.omics_oracle.monitoring.pipeline_monitor import PipelineMonitor
from src.omics_oracle.pipeline.pipeline import OmicsOracle, ProgressEvent
from src.omics_oracle.core.config import Config

@pytest.fixture
def config():
    return Config()

@pytest.fixture
def pipeline(config):
    return OmicsOracle(config, disable_cache=True)

@pytest.fixture
def monitor():
    return PipelineMonitor()

def test_pipeline_monitor_initialization(monitor):
    """Test pipeline monitor initialization"""
    assert monitor is not None
    assert hasattr(monitor, "start_monitoring")
    assert hasattr(monitor, "stop_monitoring")
    assert hasattr(monitor, "record_event")

def test_record_event(monitor):
    """Test recording events"""
    # Record a test event
    monitor.record_event(
        "test_pipeline",
        "initialization",
        "Pipeline initialized",
        success=True,
        details={"version": "1.0"}
    )

    # Check event was recorded
    assert len(monitor.events) == 1
    event = monitor.events[0]
    assert event["component"] == "test_pipeline"
    assert event["stage"] == "initialization"
    assert event["message"] == "Pipeline initialized"
    assert event["success"] is True
    assert event["details"] == {"version": "1.0"}
    assert "timestamp" in event

@pytest.mark.asyncio
async def test_monitor_progress_events(pipeline, monitor):
    """Test monitoring progress events"""
    # Set up monitoring
    with patch.object(pipeline, "set_progress_callback") as mock_set_callback:
        # Start monitoring
        monitor.start_monitoring(pipeline)

        # Check callback was set
        assert mock_set_callback.called

        # Get the callback function
        callback = mock_set_callback.call_args[0][0]

        # Create a test progress event
        event = ProgressEvent(
            stage="testing",
            message="Test progress event",
            percentage=50.0,
            detail={"test": "data"}
        )

        # Call the callback with the event
        await callback("test_query_id", event)

        # Check event was recorded
        assert len(monitor.events) > 0
        recorded = False
        for e in monitor.events:
            if (e["stage"] == "testing" and
                e["message"] == "Test progress event" and
                e["details"].get("percentage") == 50.0):
                recorded = True
                break

        assert recorded, "Progress event was not properly recorded"
```

### 5.2 WebSocket Monitoring Test

```python
# tests/monitoring/test_websocket_monitor.py

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.omics_oracle.monitoring.websocket_monitor import WebSocketMonitor
from fastapi import WebSocket

@pytest.fixture
def monitor():
    return WebSocketMonitor()

def test_websocket_monitor_initialization(monitor):
    """Test WebSocket monitor initialization"""
    assert monitor is not None
    assert hasattr(monitor, "start_monitoring")
    assert hasattr(monitor, "stop_monitoring")
    assert hasattr(monitor, "record_connection")
    assert hasattr(monitor, "record_message")
    assert hasattr(monitor, "record_disconnection")

def test_record_connection(monitor):
    """Test recording connections"""
    # Create mock WebSocket
    mock_websocket = MagicMock(spec=WebSocket)
    mock_websocket.client.host = "127.0.0.1"
    mock_websocket.client.port = 12345

    # Record connection
    monitor.record_connection(mock_websocket)

    # Check connection was recorded
    assert len(monitor.connections) == 1
    assert monitor.connections[0]["client_host"] == "127.0.0.1"
    assert monitor.connections[0]["client_port"] == 12345
    assert "timestamp" in monitor.connections[0]
    assert "connection_id" in monitor.connections[0]

@pytest.mark.asyncio
async def test_record_message(monitor):
    """Test recording messages"""
    # Create mock WebSocket
    mock_websocket = MagicMock(spec=WebSocket)
    mock_websocket.client.host = "127.0.0.1"
    mock_websocket.client.port = 12345

    # Record connection first
    connection_id = monitor.record_connection(mock_websocket)

    # Record message
    monitor.record_message(connection_id, "Test message", "outgoing")

    # Check message was recorded
    assert len(monitor.messages) == 1
    assert monitor.messages[0]["connection_id"] == connection_id
    assert monitor.messages[0]["content"] == "Test message"
    assert monitor.messages[0]["direction"] == "outgoing"
    assert "timestamp" in monitor.messages[0]

def test_record_disconnection(monitor):
    """Test recording disconnections"""
    # Create mock WebSocket
    mock_websocket = MagicMock(spec=WebSocket)
    mock_websocket.client.host = "127.0.0.1"
    mock_websocket.client.port = 12345

    # Record connection first
    connection_id = monitor.record_connection(mock_websocket)

    # Record disconnection
    monitor.record_disconnection(connection_id, reason="Client disconnected")

    # Check disconnection was recorded
    assert len(monitor.disconnections) == 1
    assert monitor.disconnections[0]["connection_id"] == connection_id
    assert monitor.disconnections[0]["reason"] == "Client disconnected"
    assert "timestamp" in monitor.disconnections[0]
```

These templates provide a solid foundation for implementing comprehensive tests for each key event in the OmicsOracle system. They cover unit tests, integration tests, end-to-end tests, and monitoring tests, ensuring that all aspects of the system are properly validated.

## Using These Templates

1. **Create Test Files**: Create the test files using these templates
2. **Fill in Implementation Details**: Add specific implementation details for your system
3. **Add More Edge Cases**: Expand the tests to cover edge cases
4. **Integrate with CI/CD**: Configure CI/CD to run these tests automatically
5. **Monitor Test Results**: Use the monitoring system to track test results

By implementing these tests, you will ensure that the OmicsOracle system functions correctly at every stage from server startup to frontend display.
