# app/services/yolo_worker.py

import asyncio

from app.services.camera_service import (
    yolo_queue,
    broadcast_to_viewers,
)
from app.services.yolo_service import run_yolo_infer


async def yolo_worker():
    """
    YOLO 전용 워커.

    ✅ 역할
    1) 카메라 프레임 큐에서 프레임 수신
    2) async YOLO 서버 호출
    3) 시청자에게 원본 프레임 + detection 결과 브로드캐스트

    ✅ 절대 하지 않는 것
    - blocking I/O
    - CPU-heavy 작업
    """

    print("[YOLO_WORKER] started")

    while True:
        try:
            # ✅ camera_service.enqueue_frame 에서 넣어준 구조
            # (source, robot_name, frame)
            source, robot_name, frame = await yolo_queue.get()

            # ✅ YOLO 추론 (비동기)
            detections = await run_yolo_infer(frame)

            # ✅ viewer에게 브로드캐스트
            await broadcast_to_viewers(
                source=source,
                robot_name=robot_name,
                frame=frame,
                detections=detections,
            )

            print(
                f"[YOLO_WORKER] {source}/{robot_name} "
                f"objects={len(detections)}"
            )

        except Exception as e:
            # 워커는 **절대 죽으면 안 된다**
            print("[YOLO_WORKER][ERROR]", e)

        finally:
            # ✅ 큐 작업 완료 표시
            yolo_queue.task_done()
