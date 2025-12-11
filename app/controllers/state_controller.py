# app/controllers/state_controller.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import math
from threading import Lock
from typing import Dict, Set

from app.services.state_history_service import enqueue_state_history
from app.services.simulation_history_service import enqueue_simulation_history

router = APIRouter(prefix="/state", tags=["state"])

print("[STATE] State WebSocket router loaded")

# ==========================================================
# 공통 상태 저장소 (실시간 viewer용)
# 실제 로봇 / 시뮬레이션 분리 관리
# ==========================================================

latest_robot_state: Dict[str, dict] = {}
latest_sim_state: Dict[str, dict] = {}

robot_viewers: Dict[str, Set[WebSocket]] = {}
sim_viewers: Dict[str, Set[WebSocket]] = {}

state_lock = Lock()

LIDAR_MAX_RANGE = 3.5


# ==========================================================
# 공통 유틸: 라이다 값 정규화
# ==========================================================
def normalize_scan_data(data: dict) -> dict:
    """
    LaserScan 데이터 정규화
    - infinity, NaN, 0 이하 → 3.5
    - 3.5 초과 → 3.5
    서버 기준에서 모든 downstream에서 동일한 품질 보장
    """
    if data.get("type") != "scan":
        return data

    ranges = data.get("data", {}).get("ranges")
    if not isinstance(ranges, list):
        return data

    normalized = []
    for r in ranges:
        if not isinstance(r, (int, float)):
            normalized.append(LIDAR_MAX_RANGE)
        elif not math.isfinite(r):
            normalized.append(LIDAR_MAX_RANGE)
        elif r <= 0.0:
            normalized.append(LIDAR_MAX_RANGE)
        elif r >= LIDAR_MAX_RANGE:
            normalized.append(LIDAR_MAX_RANGE)
        else:
            normalized.append(r)

    data["data"]["ranges"] = normalized
    return data


# ==========================================================
# 1) 실제 로봇 → Server
# ==========================================================
@router.websocket("/ws/robot/{robot_name}")
async def robot_state_ws(websocket: WebSocket, robot_name: str):
    """
    실제 로봇 상태 입력 WebSocket
    - 실시간 대시보드 브로드캐스트 O
    - teamproject DB 저장 O
    """
    await websocket.accept()
    print(f"[STATE][ROBOT] connected: {robot_name}")

    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)

            # 라이다 데이터 정규화
            data = normalize_scan_data(data)

            # 최신 상태 저장
            with state_lock:
                latest_robot_state[robot_name] = data

            # 실시간 viewer 브로드캐스트
            print(f"[STATE][ROBOT] recieved data")
            viewers = robot_viewers.get(robot_name, set())
            for ws in list(viewers):
                try:
                    await ws.send_json(data)
                except Exception:
                    viewers.discard(ws)

            # DB 히스토리 큐잉
            try:
                await enqueue_state_history(robot_name, data)
            except asyncio.QueueFull:
                pass

    except WebSocketDisconnect:
        print(f"[STATE][ROBOT] disconnected: {robot_name}")


# ==========================================================
# 2) 시뮬레이션 → Server
# ==========================================================
@router.websocket("/ws/sim/{robot_name}")
async def simulation_state_ws(websocket: WebSocket, robot_name: str):
    """
    시뮬레이션 상태 입력 WebSocket
    - 실시간 로봇 대시보드 절대 영향 없음
    - simulation DB에만 저장
    """
    await websocket.accept()
    print(f"[STATE][SIM] connected: {robot_name}")

    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)

            # 최신 상태 저장
            with state_lock:
                latest_sim_state[robot_name] = data
        
            # 실시간 viewer 브로드캐스트
            viewers = sim_viewers.get(robot_name, set())
            for ws in list(viewers):
                try:
                    await ws.send_json(data)
                except Exception:
                    viewers.discard(ws)
            
            # DB 저장
            try:
                await enqueue_simulation_history(robot_name, data)
            except asyncio.QueueFull:
                pass

    except WebSocketDisconnect:
        print(f"[STATE][SIM] disconnected: {robot_name}")


# ==========================================================
# 3) Server → 실제 로봇 대시보드
# ==========================================================
@router.websocket("/view/robot/{robot_name}")
async def robot_view_ws(websocket: WebSocket, robot_name: str):
    await websocket.accept()

    robot_viewers.setdefault(robot_name, set()).add(websocket)
    print(f"[STATE][VIEW][ROBOT] viewer +1 ({robot_name})")

    if robot_name in latest_robot_state:
        await websocket.send_json(latest_robot_state[robot_name])

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        robot_viewers[robot_name].discard(websocket)
        print(f"[STATE][VIEW][ROBOT] viewer -1 ({robot_name})")


# ==========================================================
# 4) Server → 시뮬레이션 대시보드
# ==========================================================
@router.websocket("/view/sim/{robot_name}")
async def sim_view_ws(websocket: WebSocket, robot_name: str):
    await websocket.accept()

    sim_viewers.setdefault(robot_name, set()).add(websocket)
    print(f"[STATE][VIEW][SIM] viewer +1 ({robot_name})")

    if robot_name in latest_sim_state:
        await websocket.send_json(latest_sim_state[robot_name])

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        sim_viewers[robot_name].discard(websocket)
        print(f"[STATE][VIEW][SIM] viewer -1 ({robot_name})")
