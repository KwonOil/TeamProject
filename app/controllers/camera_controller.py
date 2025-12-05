from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from app.services.camera_service import latest_frame, frame_lock, connected_clients, broadcast_frame

router = APIRouter(prefix="/camera", tags=["camera"])

# @router.post("/upload")
# async def upload_frame(file: UploadFile = File(...)):
#     frame_bytes = await file.read()

#     with frame_lock:
#         global latest_frame
#         latest_frame = frame_bytes

#     await broadcast_frame(frame_bytes)
#     return {"status": "received"}

@router.websocket("/ws/{robot_name}")
async def camera_ws(websocket: WebSocket, robot_name: str):
    await websocket.accept()
    
    try:
        while True:
            frame = await websocket.receive_bytes()

            # 로봇 이름별 최신 프레임 저장
            with frame_lock:
                latest_frame[robot_name] = frame

            # 모든 클라이언트에게 전송
            await broadcast_frame(robot_name, frame)

    except WebSocketDisconnect:
        print(f"Robot {robot_name} disconnected")
