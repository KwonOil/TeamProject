# app/controllers/camera_controller.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.camera_service import (
    enqueue_frame,
    latest_frame,
    register_viewer,
    unregister_viewer,
)
import asyncio
import json
import base64

router = APIRouter(prefix="/camera", tags=["camera"])

print("[CAMERA] Camera WebSocket router loaded")


# ==========================================================
# robot → server (카메라 업로드 전용)
# 실제 로봇은 JPEG/PNG 바이너리만 온다고 가정
# ==========================================================
@router.websocket("/ws/robot/{robot_name}")
async def robot_camera_ws(websocket: WebSocket, robot_name: str):
    await websocket.accept()
    print(f"[ROBOT][CAMERA] connected {robot_name}")

    try:
        while True:
            frame = await websocket.receive_bytes()
            print(f"[CAMERA][FRAME] {robot_name} size={len(frame)} bytes")

            # YOLO는 하지 않고 큐에만 넣기
            await enqueue_frame("robot", robot_name, frame)

    except WebSocketDisconnect:
        print(f"[ROBOT][CAMERA] disconnected {robot_name}")

    except Exception as e:
        print(f"[CAMERA][ERROR] robot {robot_name}: {e}")

# ==========================================================
# simulation → server (카메라 업로드 전용)
# - binary / base64(JSON) 둘 다 처리
# ==========================================================
@router.websocket("/ws/sim/{robot_name}")
async def simulation_camera_ws(websocket: WebSocket, robot_name: str):
    await websocket.accept()
    print(f"[SIM][CAMERA] connected {robot_name}")

    try:
        while True:
            msg = await websocket.receive()
            # print("msg:", msg)

            # ------------------------------
            # 1) 바이너리 프레임 (JPEG/PNG)
            # ------------------------------
            # Starlette 는 binary 도 'websocket.receive' 로 들어오고
            # msg 안에 'bytes' 키가 있으면 binary 프레임이다.
            if msg["type"] == "websocket.receive" and "bytes" in msg:
                frame = msg["bytes"]
                print(f"[SIM][CAMERA][FRAME] {robot_name} binary size={len(frame)}")
                await enqueue_frame("sim", robot_name, frame)
                continue

            # ------------------------------
            # 2) 텍스트(JSON + base64)
            # ------------------------------
            if msg["type"] == "websocket.receive" and "text" in msg:
                payload = json.loads(msg["text"])

                b64 = payload.get("image") or payload.get("data")
                if not b64:
                    print(f"[SIM][CAMERA] no image field: {payload.keys()}")
                    continue

                try:
                    frame = base64.b64decode(b64)
                    print(f"[SIM][CAMERA][FRAME] {robot_name} base64 size={len(frame)}")
                    await enqueue_frame("sim", robot_name, frame)
                except Exception as e:
                    print(f"[SIM][CAMERA][DECODE ERROR] {robot_name}: {e}")

    except WebSocketDisconnect:
        print(f"[SIM][CAMERA] disconnected {robot_name}")

    except Exception as e:
        print(f"[SIM][CAMERA] robot {robot_name}: {e}")

# ==========================================================
# 서버 → 실제 로봇 대시보드 (뷰어 전용)
# ==========================================================
@router.websocket("/view/robot/{robot_name}")
async def robot_viewer_ws(websocket: WebSocket, robot_name: str):
    await websocket.accept()
    # 실제 로봇 viewer 등록
    await register_viewer("robot", robot_name, websocket)

    # 이미 프레임이 있으면 바로 1장 전송
    frame = latest_frame.get("robot", {}).get(robot_name)
    if frame:
        try:
            await websocket.send_bytes(frame)
            print(f"[ROBOT][CAMERA][VIEW] sent cached frame robot={robot_name}")
        except Exception as e:
            print(f"[ROBOT][CAMERA][VIEW] cache send failed: {e}")

    try:
        while True:
            # viewer는 아무것도 안 보내도 되지만,
            # 브라우저가 ping/pong 구현이 필요하면 여기서 receive_* 호출 유지
            await websocket.receive_text()

    except WebSocketDisconnect:
        print(f"[ROBOT][CAMERA][VIEW] viewer disconnected ({robot_name})")

    finally:
        await unregister_viewer("robot", robot_name, websocket)


# ==========================================================
# 서버 → 시뮬레이션 대시보드 (뷰어 전용)
# ==========================================================
@router.websocket("/view/sim/{robot_name}")
async def sim_viewer_ws(websocket: WebSocket, robot_name: str):
    await websocket.accept()
    # 시뮬 viewer 등록
    await register_viewer("sim", robot_name, websocket)

    # 이미 프레임이 있으면 바로 1장 전송
    frame = latest_frame.get("sim", {}).get(robot_name)
    if frame:
        try:
            await websocket.send_bytes(frame)
            print(f"[SIM][CAMERA][VIEW] sent cached frame robot={robot_name}")
        except Exception as e:
            print(f"[SIM][CAMERA][VIEW] cache send failed: {e}")

    try:
        while True:
            # viewer는 아무것도 안 보내도 되지만,
            # 브라우저가 ping/pong 구현이 필요하면 여기서 receive_* 호출 유지
            await websocket.receive_text()

    except WebSocketDisconnect:
        print(f"[SIM][CAMERA][VIEW] viewer disconnected ({robot_name})")

    finally:
        await unregister_viewer("sim", robot_name, websocket)
