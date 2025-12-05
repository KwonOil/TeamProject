from sqlalchemy.orm import Session
from app.models.robot_data import RobotData

def get_latest_robot_data(db: Session, robot_name: str):
    return (
        db.query(RobotData)
        .filter(RobotData.robot_name == robot_name)
        .order_by(RobotData.id.desc())
        .first()
    )
