"""대시보드에 실시간 정보를 push 하기 위한 WebSocket 헬퍼."""
from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Set

from fastapi import WebSocket


class WebSocketManager:
    """상태/카메라 채널 구독자를 관리하는 단순 매니저."""

    def __init__(self) -> None:
        self.state_connections: Set[WebSocket] = set()
        self.camera_connections: DefaultDict[str, Set[WebSocket]] = defaultdict(set)

    async def connect_state(self, websocket: WebSocket) -> None:
        """상태 채널 연결을 수립."""

        await websocket.accept()
        self.state_connections.add(websocket)

    def disconnect_state(self, websocket: WebSocket) -> None:
        """상태 채널 연결을 제거."""

        self.state_connections.discard(websocket)

    async def broadcast_state(self, message: dict) -> None:
        """모든 상태 구독자에게 JSON 메시지를 전송."""

        for connection in list(self.state_connections):
            await connection.send_json(message)

    async def connect_camera(self, robot_id: str, websocket: WebSocket) -> None:
        """특정 로봇 카메라 채널에 연결."""

        await websocket.accept()
        self.camera_connections[robot_id].add(websocket)

    def disconnect_camera(self, robot_id: str, websocket: WebSocket) -> None:
        """카메라 채널 연결을 정리."""

        self.camera_connections[robot_id].discard(websocket)
        if not self.camera_connections[robot_id]:
            self.camera_connections.pop(robot_id, None)

    async def broadcast_camera(self, robot_id: str, data: bytes) -> None:
        """카메라 이미지 바이트를 base64 문자열로 전송."""

        import base64

        encoded = base64.b64encode(data).decode("ascii")
        payload = {"robot_id": robot_id, "image_base64": encoded}
        for connection in list(self.camera_connections.get(robot_id, set())):
            await connection.send_json(payload)

