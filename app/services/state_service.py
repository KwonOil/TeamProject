# app/services/state_service.py
from threading import Lock
from typing import Dict, Set
import asyncio
from fastapi import WebSocket

# robot_name -> 마지막 상태 메시지
latest_state: Dict[str, dict] = {}

# robot_name -> viewer WebSocket set
viewers: Dict[str, Set[WebSocket]] = {}

state_lock = Lock()

# 상태 히스토리를 DB로 넘기기 위한 비동기 큐
# 실시간 처리와 DB 저장을 분리하기 위해 사용
state_history_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)


async def register_viewer(robot_name: str, websocket: WebSocket):
    if robot_name not in viewers:
        viewers[robot_name] = set()
    viewers[robot_name].add(websocket)


async def unregister_viewer(robot_name: str, websocket: WebSocket):
    if robot_name in viewers:
        viewers[robot_name].discard(websocket)
        if not viewers[robot_name]:
            del viewers[robot_name]


async def broadcast_state(robot_name: str, state_data: dict):
    """
    로봇에서 수신한 상태 메시지를
    해당 로봇을 구독 중인 모든 대시보드로 즉시 전송
    """
    latest_state[robot_name] = state_data

    if robot_name not in viewers:
        return

    dead = set()
    for ws in viewers[robot_name]:
        try:
            await ws.send_json(state_data)
        except Exception:
            dead.add(ws)

    for ws in dead:
        viewers[robot_name].discard(ws)
