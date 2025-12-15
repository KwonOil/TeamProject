# app/services/camera_service.py

import asyncio
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
# 3) 프레임 캐시 및 viewer 목록 보호용 락
#    - asyncio.Lock 사용 (비동기 환경에서 안전)
# ---------------------------------------------------------
frame_lock = asyncio.Lock()
viewer_lock = asyncio.Lock()

# ---------------------------------------------------------
# 4) YOLO 워커용 큐
#    - (source, robot_name, frame bytes) 형태로 넣어준다.
#    - YOLO 워커는 이 정보를 이용해서
#      "어느 종류(source)의 어느 로봇(robot_name) 프레임인지"
#      를 구분해 줄 수 있다.
#    - maxsize=1 : 항상 "가장 최신" 프레임만 처리하도록 하는 정책
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
    # viewer_clients 공유 자원 보호를 위해 viewer_lock 사용
    async with viewer_lock:
        if source not in viewer_clients:
            # 혹시라도 잘못된 source 가 들어오면 방어 코드
            viewer_clients[source] = {}

        if robot_name not in viewer_clients[source]:
            viewer_clients[source][robot_name] = set()

        viewer_clients[source][robot_name].add(ws)

        total = len(viewer_clients[source][robot_name])

    print(
        f"[CAMERA][VIEW] + viewer source={source} robot={robot_name} "
        f"(total={total})"
    )


async def unregister_viewer(source: SourceType, robot_name: str, ws: WebSocket):
    """
    WebSocket 클라이언트를 viewer 목록에서 제거한다.
    - 연결이 끊겼을 때, 에러가 났을 때 호출.
    """
    async with viewer_lock:
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
    async with frame_lock:
        # source 가 없으면 방어적으로 초기화
        if source not in latest_frame:
            latest_frame[source] = {}
        latest_frame[source][robot_name] = frame

    # 2) YOLO 큐에 넣기 (큐가 꽉 차 있으면 이전 것을 버리고 최신 것만 유지)
    if yolo_queue.full():
        try:
            # 오래된 작업 하나 버리기
            _ = yolo_queue.get_nowait()
            yolo_queue.task_done()
        except asyncio.QueueEmpty:
            # 동시에 비워진 경우 등, 그냥 무시
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

    성능/안정성 포인트:
    - 느린 viewer 하나 때문에 다른 viewer 가 지연되지 않도록
      asyncio.gather 를 사용해 병렬 전송 처리.
    """

    # viewer 목록은 락을 잡고 "복사본"만 만든다.
    async with viewer_lock:
        viewers_for_source = viewer_clients.get(source)
        if not viewers_for_source:
            return

        current_viewers = viewers_for_source.get(robot_name)
        if not current_viewers:
            return

        # 실제 전송은 락 없이 하기 위해 set 복사
        viewers_snapshot = list(current_viewers)

    if not viewers_snapshot:
        return

    # 각각의 viewer 에 대한 전송 task 생성
    tasks = []
    for ws in viewers_snapshot:
        async def send_to_one(client_ws: WebSocket, f: bytes, det: list | None):
            try:
                # 1) 영상 프레임 전송
                await client_ws.send_bytes(f)

                # 2) YOLO 결과 전송 (있으면)
                if det is not None:
                    await client_ws.send_json(
                        {
                            "type": "yolo",
                            "detections": det,
                        }
                    )
            except Exception as e:
                # 예외는 상위에서 처리할 수 있도록 다시 raise
                raise e

        tasks.append(send_to_one(ws, frame, detections))

    # 병렬 전송 + 예외 수집
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 전송 실패한 소켓들 정리
    dead_clients: list[WebSocket] = []
    for ws, result in zip(viewers_snapshot, results):
        if isinstance(result, Exception):
            print(f"[CAMERA][ERROR] viewer send failed: {result}")
            dead_clients.append(ws)

    # 죽은 소켓은 viewer 목록에서 제거
    for ws in dead_clients:
        await unregister_viewer(source, robot_name, ws)
