"""
Tests for WebSocket endpoints.

Tests WebSocket connections for real-time workflow updates.
"""

import pytest
from fastapi.testclient import TestClient

from omics_oracle_v2.api.main import create_app
from omics_oracle_v2.api.websocket import connection_manager


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestWebSocketConnection:
    """Tests for WebSocket connection management."""

    def test_websocket_connect_with_workflow_id(self, client):
        """Test WebSocket connection with specific workflow ID."""
        with client.websocket_connect("/ws/workflows/test-workflow-123") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["workflow_id"] == "test-workflow-123"
            assert "message" in data

    def test_websocket_connect_dynamic_id(self, client):
        """Test WebSocket connection with dynamic workflow ID."""
        with client.websocket_connect("/ws/workflows") as websocket:
            # Should receive connection confirmation with generated ID
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "workflow_id" in data
            assert len(data["workflow_id"]) > 0  # UUID generated
            assert "message" in data

    def test_websocket_ping_pong(self, client):
        """Test WebSocket ping/pong mechanism."""
        with client.websocket_connect("/ws/workflows/test-ping") as websocket:
            # Receive connection message
            websocket.receive_json()

            # Send ping
            websocket.send_text("ping")

            # Should receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"

    def test_websocket_multiple_connections_same_workflow(self, client):
        """Test multiple clients can connect to same workflow."""
        with client.websocket_connect("/ws/workflows/shared-workflow") as ws1:
            with client.websocket_connect("/ws/workflows/shared-workflow") as ws2:
                # Both should receive connection messages
                msg1 = ws1.receive_json()
                msg2 = ws2.receive_json()

                assert msg1["type"] == "connected"
                assert msg2["type"] == "connected"
                assert msg1["workflow_id"] == msg2["workflow_id"]


class TestConnectionManager:
    """Tests for connection manager functionality."""

    @pytest.mark.asyncio
    async def test_connection_manager_send_message(self):
        """Test connection manager can send messages."""
        workflow_id = "test-send-message"
        test_message = {"type": "test", "data": "hello"}

        # Send message (no connections, should not error)
        await connection_manager.send_message(workflow_id, test_message)

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast_stage_start(self):
        """Test broadcasting stage start event."""
        workflow_id = "test-stage-start"

        await connection_manager.broadcast_stage_start(workflow_id, "query_processing", "QueryAgent")

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast_stage_complete(self):
        """Test broadcasting stage complete event."""
        workflow_id = "test-stage-complete"

        await connection_manager.broadcast_stage_complete(
            workflow_id, "query_processing", "QueryAgent", True, 150.5
        )

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast_progress(self):
        """Test broadcasting progress update."""
        workflow_id = "test-progress"

        await connection_manager.broadcast_progress(workflow_id, 50.0, "Processing...")

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast_workflow_complete(self):
        """Test broadcasting workflow completion."""
        workflow_id = "test-complete"

        await connection_manager.broadcast_workflow_complete(workflow_id, True, "Final report here")

    def test_connection_manager_get_connection_count(self):
        """Test getting connection count for workflow."""
        workflow_id = "test-count"

        # No connections initially
        count = connection_manager.get_connection_count(workflow_id)
        assert count == 0


class TestWebSocketMessages:
    """Tests for WebSocket message formats."""

    def test_websocket_receives_json_messages(self, client):
        """Test that WebSocket messages are valid JSON."""
        with client.websocket_connect("/ws/workflows/json-test") as websocket:
            data = websocket.receive_json()

            # Should be valid JSON with expected fields
            assert isinstance(data, dict)
            assert "type" in data
            assert "workflow_id" in data

    def test_websocket_connection_message_structure(self, client):
        """Test connection message has correct structure."""
        with client.websocket_connect("/ws/workflows/structure-test") as websocket:
            data = websocket.receive_json()

            # Check all expected fields
            assert data["type"] == "connected"
            assert isinstance(data["workflow_id"], str)
            assert isinstance(data["message"], str)
            assert len(data["workflow_id"]) > 0
            assert len(data["message"]) > 0


class TestWebSocketErrors:
    """Tests for WebSocket error handling."""

    def test_websocket_handles_disconnect(self, client):
        """Test WebSocket handles client disconnect gracefully."""
        with client.websocket_connect("/ws/workflows/disconnect-test") as websocket:
            # Receive connection message
            websocket.receive_json()
            # Connection will close when context exits
            # Should not raise exception

    def test_websocket_invalid_workflow_id_accepts(self, client):
        """Test WebSocket accepts any workflow ID format."""
        # Should accept various ID formats
        test_ids = [
            "123",
            "workflow-abc",
            "test_workflow_123",
            "00000000-0000-0000-0000-000000000000",
        ]

        for workflow_id in test_ids:
            with client.websocket_connect(f"/ws/workflows/{workflow_id}") as websocket:
                data = websocket.receive_json()
                assert data["workflow_id"] == workflow_id
