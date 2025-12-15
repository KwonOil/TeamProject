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

    주의점:
    - 큐에서 꺼낸 작업(item)에 대해서만 task_done() 을 호출해야 한다.
      get() 이 예외로 끝났는데도 task_done() 을 호출하면 내부 카운터가 깨진다.
    """

    print("[YOLO_WORKER] started")

    while True:
        # 1) 큐에서 작업을 하나 가져온다.
        #    이 부분은 별도의 try/finally 바깥에 둔다.
        item = await yolo_queue.get()

        try:
            # camera_service.enqueue_frame 에서 넣어준 구조
            # (source, robot_name, frame)
            source, robot_name, frame = item

            # 2) YOLO 추론 (비동기 HTTP 호출)
            detections = await run_yolo_infer(frame)

            # 3) viewer에게 브로드캐스트
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
            # ✅ 큐 작업 완료 표시 (item 이 정상적으로 꺼져온 경우에만)
            yolo_queue.task_done()
