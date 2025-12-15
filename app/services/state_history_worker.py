# app/services/state_history_worker.py

import asyncio
from datetime import datetime

from app.services.state_service import state_history_queue
from app.models.robot_state_history import RobotStateHistory
from app.config.database import SessionLocal

"""
실시간으로 들어오는 로봇 상태를 DB 에 저장하는 백그라운드 워커.

병목 개선 포인트:
- FastAPI 메인 이벤트 루프에서 DB I/O 를 직접 수행하지 않고,
  asyncio.to_thread 를 사용해 별도 스레드에서 blocking I/O 처리.
- 큐에서 꺼낸 item 구조를 검증하여, 잘못된 데이터로 인해 워커가 죽지 않도록 방어.
"""


def _save_state_history_item(item: dict) -> None:
    """
    blocking I/O (DB 작업)을 수행하는 동기 함수.
    - asyncio.to_thread 안에서 호출된다.
    - 이 함수 안에서는 동기 코드만 사용한다.
    """
    robot_name = item["robot_name"]
    msg = item["data"]

    db = SessionLocal()
    try:
        obj = RobotStateHistory(
            robot_name=robot_name,
            timestamp=datetime.utcnow(),

            pos_x=msg.get("data", {}).get("position", {}).get("x"),
            pos_y=msg.get("data", {}).get("position", {}).get("y"),

            linear_velocity=msg.get("data", {}).get("linear_vel", {}).get("x"),
            angular_velocity=msg.get("data", {}).get("angular_vel", {}).get("z"),

            battery_percentage=(
                msg.get("data", {}).get("percentage")
                if msg.get("type") == "battery"
                else None
            ),

            scan_json=(
                msg.get("data", {}).get("ranges")
                if msg.get("type") == "scan"
                else None
            ),
        )

        db.add(obj)
        db.commit()

    except Exception as e:
        db.rollback()
        print("[STATE][WORKER][ERROR]", e)

    finally:
        db.close()


async def state_history_worker():
    """
    상태 히스토리 전용 백그라운드 워커.
    - state_history_queue 에 쌓인 item 을 하나씩 꺼내 DB 에 저장한다.
    - DB I/O 는 별도 스레드에서 처리하여 이벤트 루프가 블로킹되지 않도록 한다.
    """
    print("[STATE][WORKER] history worker started")

    while True:
        # 큐에서 item 하나 가져오기 (비동기)
        item = await state_history_queue.get()

        try:
            # item 기본 구조 검증
            if not isinstance(item, dict) or "robot_name" not in item or "data" not in item:
                print("[STATE][WORKER][WARN] invalid item:", item)
            else:
                # 동기 DB 작업을 별도 스레드에서 실행
                await asyncio.to_thread(_save_state_history_item, item)

        except Exception as e:
            print("[STATE][WORKER][ERROR]", e)

        finally:
            # 큐 작업 완료 표시
            state_history_queue.task_done()
