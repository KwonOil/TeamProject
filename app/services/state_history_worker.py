# app/services/state_history_worker.py
import asyncio
from datetime import datetime
from app.services.state_service import state_history_queue
from app.models.robot_state_history import RobotStateHistory
from app.config.database import SessionLocal


async def state_history_worker():
    """
    상태 히스토리 전용 백그라운드 워커
    실시간 통신 로직과 DB I/O를 분리하기 위해 사용
    """
    print("[STATE][WORKER] history worker started")

    while True:
        item = await state_history_queue.get()

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
                )
            )

            db.add(obj)
            db.commit()

        except Exception as e:
            db.rollback()
            print("[STATE][WORKER][ERROR]", e)

        finally:
            db.close()
            state_history_queue.task_done()
