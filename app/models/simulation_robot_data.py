# app/models/simulation_robot_data.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from app.config.database_simulation import BaseSim

class SimulationRobotData(BaseSim):
    __tablename__ = "robot_data"

    id = Column(Integer, primary_key=True, index=True)
    robot_name = Column(String(50), index=True)

    timestamp = Column(DateTime, default=datetime.utcnow)

    pos_x = Column(Float)
    pos_y = Column(Float)
    pos_z = Column(Float)

    orientation_yaw = Column(Float)

    linear_velocity = Column(Float)
    angular_velocity = Column(Float)

    scan_json = Column(Text)
