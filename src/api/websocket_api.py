# websocket api 
# src/api/websocket_api.py
"""
WebSocket API für Mindestentinel (FastAPI WebSocket)
- Endpoint: /ws
- Authentifizierung: token query param `?token=<key>` oder in subprotocols (simple)
- Nachrichten-Format (JSON):
    { "type":"chat", "model":"<model_name>", "prompt":"..." }
  Antwort:
    { "type":"chat_result", "model":"<model_name>", "response":"..." }
- Nutzt ai_brain.query_async intern
"""

from __future__ import annotations
import os
import json
import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.websockets import WebSocketState

from src.api.auth import _get_expected_key  # reuse internal helper (not dependency)
_LOG = logging.getLogger("mindestentinel.websocket")
_LOG.addHandler(logging.NullHandler())

EXPECTED_KEY = os.getenv("MIND_API_KEY", None)

def _validate_token(token: Optional[str]) -> None:
    expected = EXPECTED_KEY
    if not expected:
        # In dev mode allow missing key but log warning
        _LOG.warning("MIND_API_KEY not set; WebSocket auth is permissive (dev mode).")
        return
    if not token or token != expected:
        raise HTTPException(status_code=403, detail="Invalid WebSocket token")

def create_ws_app(ai_brain) -> FastAPI:
    app = FastAPI()

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket):
        # Accept connection with optional token query param
        await websocket.accept()
        token = websocket.query_params.get("token") or websocket.headers.get("Authorization")
        try:
            _validate_token(token)
        except HTTPException as e:
            await websocket.send_json({"type":"error", "detail": str(e.detail)})
            await websocket.close(code=1008)
            return

        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    payload = json.loads(raw)
                except Exception:
                    await websocket.send_json({"type":"error", "detail":"Invalid JSON"})
                    continue

                msg_type = payload.get("type")
                if msg_type == "ping":
                    await websocket.send_json({"type":"pong"})
                    continue

                if msg_type == "chat":
                    prompt = payload.get("prompt", "")
                    models = payload.get("models", None)
                    timeout = float(payload.get("timeout", 30.0))
                    if not prompt:
                        await websocket.send_json({"type":"error", "detail":"Missing prompt field"})
                        continue
                    # call ai_brain.query_async and stream result
                    try:
                        # run query_async and get dict model->response
                        results = await ai_brain.query_async(prompt, models=models, timeout=timeout)
                        # send each model result separately
                        for mname, resp in results.items():
                            if websocket.application_state != WebSocketState.CONNECTED:
                                break
                            await websocket.send_json({"type":"chat_result", "model": mname, "response": resp})
                    except Exception as e:
                        _LOG.exception("WebSocket query error")
                        await websocket.send_json({"type":"error", "detail": str(e)})
                        continue
                else:
                    await websocket.send_json({"type":"error", "detail":"Unknown message type"})
        except WebSocketDisconnect:
            _LOG.info("WebSocket client disconnected")
        except Exception:
            _LOG.exception("Unexpected WebSocket error")
            try:
                await websocket.close()
            except Exception:
                pass

    return app
