"""
WebSocket Routes

WebSocket endpoints for real-time workflow updates.
"""

import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from omics_oracle_v2.api.websocket import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/workflows/{workflow_id}")
async def workflow_updates(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for real-time workflow updates.

    Clients can connect to this endpoint to receive real-time updates
    about workflow execution, including:
    - Stage start/completion events
    - Progress updates
    - Final results

    Args:
        websocket: WebSocket connection
        workflow_id: Workflow ID to monitor

    Example client usage (JavaScript):
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/ws/workflows/123');
        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            console.log('Update:', update);
        };
        ```
    """
    await connection_manager.connect(websocket, workflow_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "workflow_id": workflow_id,
                "message": f"Connected to workflow {workflow_id}",
            }
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Wait for client messages (ping/pong)
            data = await websocket.receive_text()

            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, workflow_id)
        logger.info(f"Client disconnected from workflow {workflow_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket, workflow_id)


@router.websocket("/workflows")
async def workflow_updates_dynamic(websocket: WebSocket):
    """
    WebSocket endpoint that assigns a new workflow ID.

    Useful for clients that don't have a workflow ID yet.
    The server will generate one and send it to the client.

    Returns:
        Sends workflow_id in first message, then handles updates
    """
    # Generate new workflow ID
    workflow_id = str(uuid.uuid4())

    await connection_manager.connect(websocket, workflow_id)

    try:
        # Send workflow ID to client
        await websocket.send_json(
            {
                "type": "connected",
                "workflow_id": workflow_id,
                "message": "New workflow session created",
            }
        )

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, workflow_id)
        logger.info(f"Client disconnected from workflow {workflow_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket, workflow_id)
