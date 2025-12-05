from sqlalchemy import Column, Integer, Float, String, DateTime, func
from app.config.database import Base

class RobotData(Base):
    __tablename__ = "robot_data"

    id = Column(Integer, primary_key=True, index=True)
    robot_name = Column(String(50))
    timestamp = Column(DateTime, server_default=func.now())
    pos_x = Column(Float)
    pos_y = Column(Float)
    pos_z = Column(Float)
    orientation_yaw = Column(Float)
    linear_velocity = Column(Float)
    angular_velocity = Column(Float)
    scan_json = Column(String)
