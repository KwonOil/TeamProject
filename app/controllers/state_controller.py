# app/controllers/state_controller.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import math
from typing import Dict, Set

from app.services.state_history_service import enqueue_state_history

router = APIRouter(prefix="/state", tags=["state"])

# ==========================================================
# Viewer 관리
# - robot_name 별로 접속 중인 WebSocket 목록
# ==========================================================
robot_viewers: Dict[str, Set[WebSocket]] = {}

# viewer 목록 동시 접근 보호
viewer_lock = asyncio.Lock()

# 라이다 최대 거리 (서버 기준 clamp 값)
LIDAR_MAX_RANGE = 3.5


# ==========================================================
# 라이다 데이터 정규화
# - NaN / inf / 0 이하 / 최대 범위 초과 값 보정
# ==========================================================
def normalize_scan_data(data: dict) -> dict:
    """
    LaserScan 데이터 정규화
    viewer / DB / 모든 downstream에서 동일한 품질 보장
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
        else:
            normalized.append(min(r, LIDAR_MAX_RANGE))

    data["data"]["ranges"] = normalized
    return data


# ==========================================================
# 1) 실제 로봇 → 서버 (상태 입력)
# ==========================================================
@router.websocket("/ws/robot/{robot_name}")
async def robot_state_ws(websocket: WebSocket, robot_name: str):
    """
    실제 로봇 상태 입력 WebSocket

    역할:
    1) viewer 실시간 브로드캐스트
    2) DB 저장용 큐에 상태 메시지 전달
    """
    await websocket.accept()
    print(f"[ROBOT][STATE] connected: {robot_name}")

    try:
        while True:
            # 로봇이 보낸 JSON 문자열 수신
            msg = await websocket.receive_text()
            data = json.loads(msg)

            # 라이다 데이터 보정
            data = normalize_scan_data(data)

            # odom 구조 정규화 (속도 키 이름 통일)
            if data.get("type") == "odom":
                odom = data.get("data", {})

                # linear_velocity / angular_velocity → twist 로 변환
                if "linear_velocity" in odom and "angular_velocity" in odom:
                    odom["twist"] = {
                        "linear": {
                            "x": odom["linear_velocity"].get("x")
                        },
                        "angular": {
                            "z": odom["angular_velocity"].get("z")
                        }
                    }
            # ------------------------------
            # viewer 브로드캐스트
            # ------------------------------
            async with viewer_lock:
                viewers = list(robot_viewers.get(robot_name, set()))

            if viewers:
                results = await asyncio.gather(
                    *[ws.send_json(data) for ws in viewers],
                    return_exceptions=True,
                )

                # 전송 실패한 WebSocket 정리
                dead = [
                    ws for ws, r in zip(viewers, results)
                    if isinstance(r, Exception)
                ]

                if dead:
                    async with viewer_lock:
                        for ws in dead:
                            robot_viewers.get(robot_name, set()).discard(ws)

            # ------------------------------
            # DB 저장 큐잉 (비동기)
            # ------------------------------
            try:
                await enqueue_state_history(robot_name, data)
            except asyncio.QueueFull:
                # 큐가 가득 찼을 경우 데이터 드롭
                pass

    except WebSocketDisconnect:
        print(f"[ROBOT][STATE] disconnected: {robot_name}")


# ==========================================================
# 2) 서버 → 대시보드 viewer
# ==========================================================
@router.websocket("/view/robot/{robot_name}")
async def robot_view_ws(websocket: WebSocket, robot_name: str):
    """
    대시보드에서 접속하는 viewer WebSocket

    - 서버는 이 소켓으로 상태를 push만 한다
    - viewer가 보내는 메시지는 무시 (keep-alive 용)
    """
    await websocket.accept()

    async with viewer_lock:
        robot_viewers.setdefault(robot_name, set()).add(websocket)

    print(f"[STATE][VIEW] viewer +1 ({robot_name})")

    try:
        while True:
            # viewer 쪽 ping/pong 대비
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        async with viewer_lock:
            robot_viewers.get(robot_name, set()).discard(websocket)
        print(f"[STATE][VIEW] viewer -1 ({robot_name})")
