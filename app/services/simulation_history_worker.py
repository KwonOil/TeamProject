# app/services/simulation_history_worker.py
import json
from datetime import datetime
from app.services.simulation_history_service import simulation_history_queue
from app.models.simulation_robot_data import SimulationRobotData
from app.config.database_simulation import SessionLocalSim


async def simulation_history_worker():
    print("[SIM][WORKER] simulation history worker started")

    while True:
        item = await simulation_history_queue.get()

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
            simulation_history_queue.task_done()
