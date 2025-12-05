from fastapi import APIRouter, Depends
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.robot_data import RobotData

import datetime

router = APIRouter(prefix="/path", tags=["path"])

templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def path_page(request: Request):
    return templates.TemplateResponse("path.html", {"request": request})


@router.get("/api")
def get_robot_path(robot_name: str, db: Session = Depends(get_db)):
    rows = (
        db.query(RobotData)
        .filter(RobotData.robot_name == robot_name)
        .order_by(RobotData.timestamp.asc())
        .all()
    )

    path = [
        {"x": r.pos_x, "y": r.pos_y, "t": r.timestamp}
        for r in rows
        if r.pos_x is not None and r.pos_y is not None
    ]

    return {"path": path}
@router.get("/api/robot/{robot_name}/path")
def get_robot_path(robot_name: str, start: str, end: str, db: Session = Depends(get_db)):
    # 문자열 → datetime 변환
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    rows = (
        db.query(RobotData)
        .filter(RobotData.robot_name == robot_name)
        .filter(RobotData.timestamp >= start_dt)
        .filter(RobotData.timestamp <= end_dt)
        .order_by(RobotData.timestamp.asc())
        .all()
    )

    return {
        "points": [
            {"x": r.pos_x, "y": r.pos_y, "t": r.timestamp.isoformat()}
            for r in rows
        ]
    }