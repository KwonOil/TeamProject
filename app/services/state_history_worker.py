# app/services/state_history_worker.py

import asyncio
from datetime import datetime

from app.config.database import SessionLocal
from app.models.robot_state_history import RobotStateHistory
from app.services.state_service import state_history_queue


async def state_history_worker():
    """
    상태 히스토리 DB 저장 Worker

    - WebSocket 수신 즉시 enqueue 된 데이터를 처리
    - odom 메시지를 받는 즉시 DB에 INSERT
    - 구조는 비동기, DB I/O는 동기 (현실적 타협)
    """
    print("[STATE_HISTORY_WORKER] started")

    while True:
        item = await state_history_queue.get()

        robot_name = item["robot_name"]
        data = item["data"]
        msg_type = data.get("type")

        # odom만 저장
        if msg_type != "odom":
            continue

        odom = data.get("data")
        if not odom:
            continue

        pos = odom.get("position")
        twist = odom.get("twist")

        if not pos or not twist:
            continue

        record = RobotStateHistory(
            robot_name=robot_name,

            pos_x=pos.get("x"),
            pos_y=pos.get("y"),

            # odom 기반 실제 속도
            linear_velocity=twist.get("linear", {}).get("x"),
            angular_velocity=twist.get("angular", {}).get("z"),

            battery_percentage=None,
            scan_json=None,
            timestamp=datetime.utcnow(),
        )

        # DB는 try 바깥에서 열지 않는다
        db = SessionLocal()
        try:
            db.add(record)
            db.commit()
            print(f"[DB][OK] saved odom {robot_name}")

        except Exception as e:
            db.rollback()
            print("[DB][ERROR]", e)

        finally:
            db.close()
