# app/services/state_service.py

import asyncio
from typing import Dict, Set
from fastapi import WebSocket

# robot_name -> 마지막 상태 메시지
latest_state: Dict[str, dict] = {}

# robot_name -> viewer WebSocket set
viewers: Dict[str, Set[WebSocket]] = {}

# asyncio 환경용 Lock
state_lock = asyncio.Lock()
viewer_lock = asyncio.Lock()

# 상태 히스토리를 DB로 넘기기 위한 비동기 큐
state_history_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)


async def register_viewer(robot_name: str, websocket: WebSocket):
    async with viewer_lock:
        viewers.setdefault(robot_name, set()).add(websocket)


async def unregister_viewer(robot_name: str, websocket: WebSocket):
    async with viewer_lock:
        if robot_name in viewers:
            viewers[robot_name].discard(websocket)
            if not viewers[robot_name]:
                del viewers[robot_name]


async def broadcast_state(robot_name: str, state_data: dict):
    """
    로봇 상태를 모든 viewer에 전송
    """
    async with state_lock:
        latest_state[robot_name] = state_data

    async with viewer_lock:
        targets = list(viewers.get(robot_name, set()))

    dead = []
    for ws in targets:
        try:
            await ws.send_json(state_data)
        except Exception:
            dead.append(ws)

    if dead:
        async with viewer_lock:
            for ws in dead:
                viewers.get(robot_name, set()).discard(ws)
