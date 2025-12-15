# app/services/simulation_history_worker.py

import json
import asyncio
from datetime import datetime

from app.services.simulation_history_service import simulation_history_queue
from app.models.simulation_robot_data import SimulationRobotData
from app.config.database_simulation import SessionLocalSim

"""
시뮬레이션 로봇 상태를 DB 에 저장하는 백그라운드 워커.

실제 로봇과 마찬가지로,
DB I/O 는 asyncio.to_thread 를 통해 별도 스레드에서 처리한다.
"""


def _save_simulation_history_item(item: dict) -> None:
    """
    시뮬레이션 상태를 DB 에 저장하는 blocking I/O 함수.
    asyncio.to_thread 로 호출된다.
    """
    robot_name = item["robot_name"]
    msg = item["data"]

    db = SessionLocalSim()
    try:
        obj = SimulationRobotData(
            robot_name=robot_name,
            timestamp=datetime.utcnow(),

            pos_x=msg.get("data", {}).get("position", {}).get("x"),
            pos_y=msg.get("data", {}).get("position", {}).get("y"),
            pos_z=None,

            orientation_yaw=None,

            linear_velocity=msg.get("data", {}).get("linear_vel", {}).get("x"),
            angular_velocity=msg.get("data", {}).get("angular_vel", {}).get("z"),

            scan_json=json.dumps(msg.get("data", {}).get("ranges"))
            if msg.get("type") == "scan"
            else None,
        )

        db.add(obj)
        db.commit()

    except Exception as e:
        db.rollback()
        print("[SIM][WORKER][ERROR]", e)

    finally:
        db.close()


async def simulation_history_worker():
    print("[SIM][WORKER] simulation history worker started")

    while True:
        item = await simulation_history_queue.get()

        try:
            if not isinstance(item, dict) or "robot_name" not in item or "data" not in item:
                print("[SIM][WORKER][WARN] invalid item:", item)
            else:
                await asyncio.to_thread(_save_simulation_history_item, item)

        except Exception as e:
            print("[SIM][WORKER][ERROR]", e)

        finally:
            simulation_history_queue.task_done()
