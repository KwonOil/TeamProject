# app/services/state_history_worker.py
# 상태 히스토리 DB 저장 Worker
import asyncio
from datetime import datetime

from app.config.database import SessionLocal
from app.models.robot_state_history import RobotStateHistory
from app.services.state_history_queue import state_history_queue


async def state_history_worker():
    """
    상태 히스토리 DB 저장 Worker

    정책:
    - 메시지 1개 = DB row 1개
    - 타입별로 채울 수 있는 컬럼만 채운다
    - 나머지는 NULL
    """

    print("[STATE_HISTORY_WORKER] started")

    while True:
        item = await state_history_queue.get()

        robot_name = item["robot_name"]
        data = item["data"]
        msg_type = data.get("type")
        payload = data.get("data", {})

        # 기본값은 전부 None
        record_kwargs = {
            "robot_name": robot_name,
            "timestamp": datetime.utcnow(),
            "pos_x": None,
            "pos_y": None,
            "linear_velocity": None,
            "angular_velocity": None,
            "battery_percentage": None,
            "scan_json": None,
        }

        # -----------------------------
        # 타입별 매핑
        # -----------------------------
        if msg_type == "odom":
            pos = payload.get("position", {})
            lin = payload.get("linear_velocity", {})
            ang = payload.get("angular_velocity", {})

            record_kwargs.update({
                "pos_x": pos.get("x"),
                "pos_y": pos.get("y"),
                "linear_velocity": lin.get("x"),
                "angular_velocity": ang.get("z"),
            })

        elif msg_type == "battery":
            record_kwargs["battery_percentage"] = payload.get("percentage")

        elif msg_type == "scan":
            record_kwargs["scan_json"] = payload

        else:
            # 저장할 가치 없는 타입
            continue

        # -----------------------------
        # DB INSERT
        # -----------------------------
        db = SessionLocal()
        try:
            record = RobotStateHistory(**record_kwargs)
            db.add(record)
            db.commit()
            print(f"[DB][OK] saved {msg_type} {robot_name}")

        except Exception as e:
            db.rollback()
            print("[DB][ERROR]", e)

        finally:
            db.close()
