"""
WebSocket Connection Manager

Manages WebSocket connections for real-time workflow updates.
"""

import json
import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for workflow updates."""

    def __init__(self):
        """Initialize connection manager."""
        # workflow_id -> list of websocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, workflow_id: str):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
            workflow_id: Workflow ID to associate with connection
        """
        await websocket.accept()
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = []
        self.active_connections[workflow_id].append(websocket)
        logger.info(f"WebSocket connected for workflow {workflow_id}")

    def disconnect(self, websocket: WebSocket, workflow_id: str):
        """
        Unregister a WebSocket connection.

        Args:
            websocket: WebSocket connection to unregister
            workflow_id: Associated workflow ID
        """
        if workflow_id in self.active_connections:
            if websocket in self.active_connections[workflow_id]:
                self.active_connections[workflow_id].remove(websocket)
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]
        logger.info(f"WebSocket disconnected for workflow {workflow_id}")

    async def send_message(self, workflow_id: str, message: dict):
        """
        Send a message to all connections for a workflow.

        Args:
            workflow_id: Workflow ID
            message: Message dictionary to send
        """
        if workflow_id not in self.active_connections:
            return

        # Convert message to JSON
        message_json = json.dumps(message)

        # Send to all connections for this workflow
        disconnected = []
        for connection in self.active_connections[workflow_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, workflow_id)

    async def broadcast_stage_start(self, workflow_id: str, stage: str, agent_name: str):
        """
        Broadcast workflow stage start event.

        Args:
            workflow_id: Workflow ID
            stage: Stage name
            agent_name: Agent executing the stage
        """
        await self.send_message(
            workflow_id,
            {
                "type": "stage_start",
                "workflow_id": workflow_id,
                "stage": stage,
                "agent_name": agent_name,
            },
        )

    async def broadcast_stage_complete(
        self,
        workflow_id: str,
        stage: str,
        agent_name: str,
        success: bool,
        execution_time_ms: float,
        error: str = None,
    ):
        """
        Broadcast workflow stage completion event.

        Args:
            workflow_id: Workflow ID
            stage: Stage name
            agent_name: Agent that executed the stage
            success: Whether stage succeeded
            execution_time_ms: Stage execution time
            error: Error message if failed
        """
        await self.send_message(
            workflow_id,
            {
                "type": "stage_complete",
                "workflow_id": workflow_id,
                "stage": stage,
                "agent_name": agent_name,
                "success": success,
                "execution_time_ms": execution_time_ms,
                "error": error,
            },
        )

    async def broadcast_progress(self, workflow_id: str, progress_percentage: float, message: str):
        """
        Broadcast workflow progress update.

        Args:
            workflow_id: Workflow ID
            progress_percentage: Progress percentage (0-100)
            message: Progress message
        """
        await self.send_message(
            workflow_id,
            {
                "type": "progress",
                "workflow_id": workflow_id,
                "progress": progress_percentage,
                "message": message,
            },
        )

    async def broadcast_workflow_complete(
        self, workflow_id: str, success: bool, final_report: str = None, error: str = None
    ):
        """
        Broadcast workflow completion event.

        Args:
            workflow_id: Workflow ID
            success: Whether workflow succeeded
            final_report: Final report if successful
            error: Error message if failed
        """
        await self.send_message(
            workflow_id,
            {
                "type": "workflow_complete",
                "workflow_id": workflow_id,
                "success": success,
                "final_report": final_report,
                "error": error,
            },
        )

    def get_connection_count(self, workflow_id: str) -> int:
        """
        Get number of active connections for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(workflow_id, []))


# Global connection manager instance
connection_manager = ConnectionManager()
