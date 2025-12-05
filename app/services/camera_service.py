import asyncio
import threading

# 각 로봇별 최신 프레임 저장
latest_frame = {}   # {"tb3_1": frame_bytes, "tb3_2": frame_bytes}

# 로봇별 WebSocket 클라이언트 목록
connected_clients = {}  # {"tb3_1": set([...]), "tb3_2": set([...])}

frame_lock = threading.Lock()


async def broadcast_frame(robot_name: str, frame: bytes):
    """해당 robot_name과 연결된 WebSocket 클라이언트에게만 프레임 전송"""
    
    if robot_name not in connected_clients:
        return
    
    dead = []

    for ws in connected_clients[robot_name]:
        try:
            await ws.send_bytes(frame)
        except:
            dead.append(ws)

    # 연결이 끊긴 websocket 제거
    for ws in dead:
        connected_clients[robot_name].remove(ws)
