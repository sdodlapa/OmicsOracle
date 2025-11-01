#!/usr/bin/env python3
"""
Test WebSocket connection for live monitoring
"""

import asyncio
import json

import websockets


async def test_websocket():
    uri = "ws://localhost:8001/ws/monitor"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")

            # Keep connection alive and listen for messages
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"📨 Received: {message}")
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send("ping")
                    print("📡 Sent ping")

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")


if __name__ == "__main__":
    print("🔍 Testing WebSocket connection...")
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n🛑 Test stopped")
