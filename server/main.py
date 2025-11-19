"""운전연수 프로젝트 FastAPI 진입점."""
from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .api.robots import router as robot_router
from .api.yolo import router as yolo_router
from .services.robot_state_manager import RobotStateManager
from .services.websocket_manager import WebSocketManager
from .services.yolo_service import YOLOService

app = FastAPI(title="운전연수 프로젝트 서버", version="0.1.0")

# 애플리케이션 전역 상태에 매니저 인스턴스 등록
app.state.robot_state_manager = RobotStateManager()
app.state.websocket_manager = WebSocketManager()
app.state.yolo_service = YOLOService()

# REST 라우터 등록
app.include_router(robot_router)
app.include_router(yolo_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """배포 환경에서 살아있는지 확인하기 위한 간단한 엔드포인트."""

    return {"status": "ok"}


@app.websocket("/ws/robots/state")
async def websocket_robot_state(websocket: WebSocket) -> None:
    """대시보드가 모든 로봇 상태를 받을 수 있는 실시간 채널."""

    ws_manager: WebSocketManager = app.state.websocket_manager
    await ws_manager.connect_state(websocket)
    try:
        while True:
            # 대시보드 → 서버 메시지는 현재 사용하지 않으므로 대기만 수행
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_state(websocket)


@app.websocket("/ws/robots/{robot_id}/camera")
async def websocket_robot_camera(robot_id: str, websocket: WebSocket) -> None:
    """각 로봇의 카메라 스트림을 대시보드로 중계."""

    ws_manager: WebSocketManager = app.state.websocket_manager
    await ws_manager.connect_camera(robot_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_camera(robot_id, websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)

