from sqlalchemy.orm import Session
from app.models.robot_state_history import RobotStateHistory

def get_latest_robot_data(db: Session, robot_name: str):
    return (
        db.query(RobotStateHistory)
        .filter(RobotStateHistory.robot_name == robot_name)
        .order_by(RobotStateHistory.id.desc())
        .first()
    )
