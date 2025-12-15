# app/services/control_service.py

from typing import Dict
from fastapi import WebSocket
import asyncio


# ==========================================================
# 로봇 이름 → 해당 로봇과 연결된 제어 WebSocket
# ==========================================================
_control_sockets: Dict[str, WebSocket] = {}

# 동시 접근 보호용 async Lock
_control_lock = asyncio.Lock()


async def register_robot_control_ws(robot_name: str, websocket: WebSocket) -> None:
    """
    로봇이 /control/ws/robot/{robot_name} 로 접속하면
    WebSocket 을 등록한다.

    - 동일 이름 로봇이 재접속하면 기존 소켓을 덮어쓴다.
    """
    async with _control_lock:
        _control_sockets[robot_name] = websocket

    print(f"[CONTROL][REGISTER] robot={robot_name}")


async def unregister_robot_control_ws(robot_name: str, websocket: WebSocket) -> None:
    """
    로봇 WebSocket 연결이 끊어질 때 등록 해제.
    """
    async with _control_lock:
        cur = _control_sockets.get(robot_name)
        if cur is websocket:
            del _control_sockets[robot_name]
            print(f"[CONTROL][UNREGISTER] robot={robot_name}")


async def send_control_command(robot_name: str, command: dict) -> bool:
    """
    지정한 로봇에게 제어 명령(JSON)을 전송한다.

    반환값:
    - True  : 전송 성공
    - False : 로봇 미연결 또는 전송 실패

    변경점:
    - WebSocket 조회와 실제 전송을 하나의 Lock 범위 안에 넣어
      전송 중 소켓이 바뀌는 race condition 을 방지한다.
    """
    async with _control_lock:
        ws = _control_sockets.get(robot_name)

        if ws is None:
            print(f"[CONTROL][WARN] robot '{robot_name}' is not connected")
            return False

        try:
            await ws.send_json(command)
            print(f"[CONTROL][SEND] robot={robot_name} cmd={command}")
            return True

        except Exception as e:
            print(f"[CONTROL][ERROR] send failed robot={robot_name}: {e}")

            # 실패한 소켓은 제거 (유령 연결 방지)
            cur = _control_sockets.get(robot_name)
            if cur is ws:
                del _control_sockets[robot_name]

            return False
