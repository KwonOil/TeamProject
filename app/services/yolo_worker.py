# app/services/yolo_worker.py

import asyncio

from app.services.camera_service import (
    yolo_queue,
    broadcast_to_viewers,
)
from app.services.yolo_service import run_yolo_infer


async def yolo_worker():
    """
    YOLO 전용 워커 (최신 프레임만 처리)

    =========================================================
    역할
    ---------------------------------------------------------
    1) 카메라 프레임 큐에서 프레임 수신
    2) 큐에 쌓인 오래된 프레임은 모두 버림
    3) 가장 최신 프레임 1장만 YOLO 추론
    4) 결과를 viewer에게 브로드캐스트

    =========================================================
    설계 철학
    ---------------------------------------------------------
    - YOLO는 실시간성이 중요 → backlog 금지
    - timeout은 오류가 아니라 "프레임 드롭"
    - 항상 "지금"을 본다

    =========================================================
    절대 하지 않는 것
    ---------------------------------------------------------
    - CPU blocking 작업
    - 큐를 무한히 처리하는 구조
    - 워커 종료
    """

    print("[YOLO_WORKER] started (latest-frame-only mode)")

    while True:
        # -----------------------------------------------------
        # 1) 최소 1개의 프레임을 기다린다
        # -----------------------------------------------------
        item = await yolo_queue.get()

        # 최신 프레임으로 교체될 변수
        latest_item = item

        try:
            # -------------------------------------------------
            # 2) 큐에 남아 있는 모든 프레임을 비운다
            #    (가장 마지막 것만 유지)
            # -------------------------------------------------
            while True:
                try:
                    old_item = yolo_queue.get_nowait()
                    latest_item = old_item

                    # 버리는 프레임도 task_done 호출
                    yolo_queue.task_done()
                except asyncio.QueueEmpty:
                    break

            # -------------------------------------------------
            # 3) 최신 프레임만 처리
            # -------------------------------------------------
            source, robot_name, frame = latest_item

            try:
                detections = await run_yolo_infer(frame)
            except Exception as e:
                # YOLO timeout / 네트워크 에러는 정상적인 상황
                print(f"[YOLO][DROP] {source}/{robot_name} reason={e}")
                continue

            # -------------------------------------------------
            # 4) viewer에게 결과 브로드캐스트
            # -------------------------------------------------
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
            # 워커는 절대 죽지 않는다
            print("[YOLO_WORKER][ERROR]", e)

        finally:
            # 최초 get() 에 대한 task_done
            yolo_queue.task_done()
