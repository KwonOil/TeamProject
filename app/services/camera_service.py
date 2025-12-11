# app/services/camera_service.py
import asyncio
from threading import Lock
from typing import Dict, Set, Tuple, Literal

from fastapi import WebSocket

# ---------------------------------------------------------
#  타입 정의
# ---------------------------------------------------------
# source 는 "robot" 또는 "sim" 둘 중 하나만 허용
SourceType = Literal["robot", "sim"]

# ---------------------------------------------------------
# 1) 최신 프레임 캐시
#    - source ("robot" / "sim") 기준으로 분리
#    - 각 source 안에서 robot_name 으로 다시 분리
#      latest_frame["robot"]["tb3_1"]  -> 실제 로봇 tb3_1 의 최근 프레임
#      latest_frame["sim"]["tb3_1"]    -> 시뮬 tb3_1 의 최근 프레임
# ---------------------------------------------------------
latest_frame: Dict[SourceType, Dict[str, bytes]] = {
    "robot": {},
    "sim": {},
}

# ---------------------------------------------------------
# 2) viewer WebSocket 목록
#    - 마찬가지로 source / robot_name 단위로 관리
#      viewer_clients["robot"]["tb3_1"] -> 실제 로봇 tb3_1 화면 보는 브라우저들
#      viewer_clients["sim"]["tb3_1"]   -> 시뮬 tb3_1 화면 보는 브라우저들
# ---------------------------------------------------------
viewer_clients: Dict[SourceType, Dict[str, Set[WebSocket]]] = {
    "robot": {},
    "sim": {},
}

# ---------------------------------------------------------
# 3) 프레임 캐시 보호용 락
#    - latest_frame 에 동시에 쓰는 상황 대비
# ---------------------------------------------------------
frame_lock = Lock()

# ---------------------------------------------------------
# 4) YOLO 워커용 큐
#    - (source, robot_name, frame bytes) 형태로 넣어준다.
#    - YOLO 워커는 이 정보를 이용해서
#      "어느 종류(source)의 어느 로봇(robot_name) 프레임인지"
#      를 구분해 줄 수 있다.
# ---------------------------------------------------------
yolo_queue: asyncio.Queue[Tuple[SourceType, str, bytes]] = asyncio.Queue(
    maxsize=1
)


# =========================================================
# viewer 등록 / 해제
# =========================================================
async def register_viewer(source: SourceType, robot_name: str, ws: WebSocket):
    """
    특정 source("robot"/"sim") 의 특정 로봇 화면을 보고 싶어 하는
    WebSocket 클라이언트를 등록한다.

    예)
      /camera/view/robot/tb3_1  -> source="robot", robot_name="tb3_1"
      /camera/view/sim/tb3_1    -> source="sim",   robot_name="tb3_1"
    """
    if source not in viewer_clients:
        # 혹시라도 잘못된 source 가 들어오면 방어 코드
        viewer_clients[source] = {}

    if robot_name not in viewer_clients[source]:
        viewer_clients[source][robot_name] = set()

    viewer_clients[source][robot_name].add(ws)
    print(
        f"[CAMERA][VIEW] + viewer source={source} robot={robot_name} "
        f"(total={len(viewer_clients[source][robot_name])})"
    )


async def unregister_viewer(source: SourceType, robot_name: str, ws: WebSocket):
    """
    WebSocket 클라이언트를 viewer 목록에서 제거한다.
    - 연결이 끊겼을 때, 에러가 났을 때 호출.
    """
    if source in viewer_clients and robot_name in viewer_clients[source]:
        viewer_clients[source][robot_name].discard(ws)

        # 더 이상 아무도 안 보고 있으면 key 정리
        if not viewer_clients[source][robot_name]:
            del viewer_clients[source][robot_name]

    print(f"[CAMERA][VIEW] - viewer source={source} robot={robot_name}")


# =========================================================
# 프레임 enqueue (로봇/시뮬 → 서버)
# =========================================================
async def enqueue_frame(source: SourceType, robot_name: str, frame: bytes):
    """
    로봇(실제 또는 시뮬레이션)에서 받은 프레임을 처리한다.

    1) latest_frame[source][robot_name] 에 저장
       - 새로 화면을 여는 viewer에게 첫 프레임으로 보내기 위함
    2) YOLO 워커 큐에 (source, robot_name, frame) 를 넣어준다.
       - YOLO 결과를 계산해서 시청중인 viewer들에게 브로드캐스트할 수 있도록.
    """
    # 1) 최신 프레임 캐시 갱신
    with frame_lock:
        # source 가 없으면 방어적으로 초기화
        if source not in latest_frame:
            latest_frame[source] = {}
        latest_frame[source][robot_name] = frame

    # 2) YOLO 큐에 넣기 (큐가 꽉 차 있으면 이전 것을 버리고 최신 것만 유지)
    if yolo_queue.full():
        try:
            yolo_queue.get_nowait()
            yolo_queue.task_done()
        except asyncio.QueueEmpty:
            # 동시에 비운 경우 등, 그냥 무시
            pass

    await yolo_queue.put((source, robot_name, frame))


# =========================================================
# YOLO 워커 → viewer 브로드캐스트
# =========================================================
async def broadcast_to_viewers(
    source: SourceType,
    robot_name: str,
    frame: bytes,
    detections: list | None = None,
):
    """
    YOLO 워커가 호출하는 브로드캐스트 함수.

    동일한 source & robot_name 을 구독 중인 모든 viewer 에게
    1) 영상 프레임
    2) YOLO 결과(JSON, 선택적)
    를 전송한다.
    """
    # source / robot_name 에 해당하는 viewer 목록 가져오기
    viewers_for_source = viewer_clients.get(source)
    if not viewers_for_source:
        return

    viewers = viewers_for_source.get(robot_name)
    if not viewers:
        return

    dead: list[WebSocket] = []

    for ws in list(viewers):
        try:
            # 1) 영상 프레임 전송
            await ws.send_bytes(frame)

            # 2) YOLO 결과 전송 (있으면)
            if detections is not None:
                await ws.send_json(
                    {
                        "type": "yolo",
                        "detections": detections,
                    }
                )

        except Exception as e:
            # 전송 실패한 소켓은 나중에 정리
            print(f"[CAMERA][ERROR] viewer send failed: {e}")
            dead.append(ws)

    # 끊어진 소켓 정리
    for ws in dead:
        await unregister_viewer(source, robot_name, ws)
