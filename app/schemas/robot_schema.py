# app/schemas/robot_schema.py
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class RobotStatus(BaseModel):
    robot_name: str
    timestamp: datetime
    pos_x: Optional[float]
    pos_y: Optional[float]
    pos_z: Optional[float]
    orientation_yaw: Optional[float]
    linear_velocity: Optional[float]
    angular_velocity: Optional[float]
    scan_json: List[Optional[float]]

    class Config:
        orm_mode = True
