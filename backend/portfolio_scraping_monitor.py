"""
WebSocket/SSE endpoint for portfolio scraping progress monitoring
Provides real-time updates to frontend
"""
import asyncio
import json
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import queue
import threading

router = APIRouter()

# Store progress events for each scraping session
scraping_sessions: Dict[str, queue.Queue] = {}


def get_progress_callback(session_id: str):
    """Create progress callback for a scraping session"""
    # Ensure session queue exists
    if session_id not in scraping_sessions:
        scraping_sessions[session_id] = queue.Queue()
    
    def callback(event: Dict):
        if session_id in scraping_sessions:
            scraping_sessions[session_id].put(event)
            print(f"[MONITOR] Event queued for session {session_id}: {event.get('type', 'unknown')}")
        else:
            print(f"[MONITOR] WARNING: Session {session_id} not found in scraping_sessions")
    return callback


@router.websocket("/ws/portfolio-scraping/{session_id}")
async def websocket_portfolio_scraping(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time scraping progress"""
    await websocket.accept()
    
    if session_id not in scraping_sessions:
        scraping_sessions[session_id] = queue.Queue()
    
    try:
        while True:
            # Check for new events
            try:
                event = scraping_sessions[session_id].get_nowait()
                await websocket.send_json(event)
            except queue.Empty:
                await asyncio.sleep(0.5)  # Poll every 500ms
    except WebSocketDisconnect:
        # Clean up session
        if session_id in scraping_sessions:
            del scraping_sessions[session_id]


@router.get("/sse/portfolio-scraping/{session_id}")
async def sse_portfolio_scraping(session_id: str):
    """Server-Sent Events endpoint for scraping progress"""
    if EventSourceResponse is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=501, detail="SSE not available. Install sse-starlette.")
    
    async def event_generator():
        if session_id not in scraping_sessions:
            scraping_sessions[session_id] = queue.Queue()
        
        while True:
            try:
                event = scraping_sessions[session_id].get(timeout=1)
                yield {
                    "event": "progress",
                    "data": json.dumps(event)
                }
            except queue.Empty:
                yield {
                    "event": "ping",
                    "data": json.dumps({"type": "ping"})
                }
    
    return EventSourceResponse(event_generator())

