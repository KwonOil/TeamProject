# app/models/robot_state_history.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from app.config.database import Base
from datetime import datetime

class RobotStateHistory(Base):
    __tablename__ = "robot_state_history"

    id = Column(Integer, primary_key=True, index=True)
    robot_name = Column(String, index=True, nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    pos_x = Column(Float)
    pos_y = Column(Float)

    linear_velocity = Column(Float)
    angular_velocity = Column(Float)

    battery_percentage = Column(Float)

    # 라이다 전체 또는 요약본
    scan_json = Column(JSON)
