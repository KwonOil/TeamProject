# app/controllers/state_controller.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import math
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

# 상태/뷰어 관련 공유 자원 보호용 Lock
# asyncio 환경에서는 threading.Lock 이 아니라 asyncio.Lock 사용
state_lock = asyncio.Lock()
viewer_lock = asyncio.Lock()

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
    print(f"[ROBOT][STATE] connected: {robot_name}")

    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)

            # 라이다 데이터 정규화
            data = normalize_scan_data(data)

            # 최신 상태 저장 (동시 접근 보호)
            async with state_lock:
                latest_robot_state[robot_name] = data

            # 실시간 viewer 브로드캐스트
            print(f"[ROBOT][STATE] recieved data")

            # viewer 목록은 락을 잡고 복사본만 가져온다.
            async with viewer_lock:
                viewers = list(robot_viewers.get(robot_name, set()))

            if viewers:
                # 각각 viewer 에 대해 병렬 전송
                tasks = [ws.send_json(data) for ws in viewers]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 전송 실패한 소켓은 제거
                dead = [
                    ws for ws, result in zip(viewers, results)
                    if isinstance(result, Exception)
                ]

                if dead:
                    async with viewer_lock:
                        for ws in dead:
                            robot_viewers.get(robot_name, set()).discard(ws)

            # DB 히스토리 큐잉
            try:
                await enqueue_state_history(robot_name, data)
            except asyncio.QueueFull:
                # 큐가 가득 찬 경우, 데이터를 버리는 정책을 사용
                # (로그 추가를 원하면 여기에서 print 로 남기면 됨)
                pass

    except WebSocketDisconnect:
        print(f"[ROBOT][STATE] disconnected: {robot_name}")


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
    print(f"[SIM][STATE] connected: {robot_name}")

    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)

            # 최신 상태 저장
            async with state_lock:
                latest_sim_state[robot_name] = data

            # 실시간 viewer 브로드캐스트
            async with viewer_lock:
                viewers = list(sim_viewers.get(robot_name, set()))

            if viewers:
                tasks = [ws.send_json(data) for ws in viewers]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                dead = [
                    ws for ws, result in zip(viewers, results)
                    if isinstance(result, Exception)
                ]

                if dead:
                    async with viewer_lock:
                        for ws in dead:
                            sim_viewers.get(robot_name, set()).discard(ws)

            # DB 저장
            try:
                await enqueue_simulation_history(robot_name, data)
            except asyncio.QueueFull:
                # 큐가 가득 찬 경우 처리 정책 (현재는 조용히 버림)
                pass

    except WebSocketDisconnect:
        print(f"[SIM][STATE] disconnected: {robot_name}")


# ==========================================================
# 3) Server → 실제 로봇 대시보드
# ==========================================================
@router.websocket("/view/robot/{robot_name}")
async def robot_view_ws(websocket: WebSocket, robot_name: str):
    await websocket.accept()
    
    # viewer 등록 (동시성 보호)
    async with viewer_lock:
        robot_viewers.setdefault(robot_name, set()).add(websocket)
    print(f"[ROBOT][STATE][VIEW] viewer +1 ({robot_name})")

    # 기존 최신 상태가 있으면 즉시 한 번 보내기
    async with state_lock:
        initial_state = latest_robot_state.get(robot_name)

    if initial_state:
        await websocket.send_json(initial_state)

    try:
        while True:
            msg = await websocket.receive_json()
            await websocket.send_json(msg)
            # viewer 쪽에서 ping/pong 혹은 keep-alive 용으로
            # 메시지를 보낼 경우를 대비해 receive 유지
            # await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"[ROBOT][STATE][WS DISCONNECT] {robot_name}")
    finally:
        async with viewer_lock:
            robot_viewers.get(robot_name, set()).discard(websocket)
        print(f"[ROBOT][STATE][VIEW] viewer -1 ({robot_name})")


# ==========================================================
# 4) Server → 시뮬레이션 대시보드
# ==========================================================
@router.websocket("/view/sim/{robot_name}")
async def sim_view_ws(websocket: WebSocket, robot_name: str):
    await websocket.accept()

    async with viewer_lock:
        sim_viewers.setdefault(robot_name, set()).add(websocket)
    print(f"[SIM][STATE][VIEW] viewer +1 ({robot_name})")

    async with state_lock:
        initial_state = latest_sim_state.get(robot_name)

    if initial_state:
        await websocket.send_json(initial_state)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        async with viewer_lock:
            sim_viewers.get(robot_name, set()).discard(websocket)
        print(f"[SIM][STATE][VIEW] viewer -1 ({robot_name})")
