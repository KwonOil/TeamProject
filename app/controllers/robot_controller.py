# app/controllers/robot_controller.py
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import math
import json

from app.config.database import get_db
from app.models.robot_data import RobotData

router = APIRouter(prefix="/robot", tags=["robot"])
templates = Jinja2Templates(directory="app/templates")


# ---------- 1) 최근 상태 JSON API ----------

@router.get("/status")
def get_status(robot_name: str, db: Session = Depends(get_db)):
    """
    특정 로봇의 가장 최신 상태 1건을 반환하는 API.
    - 위치, 속도, 회전, 스캔 데이터 등을 포함.
    - scan_json 안의 Infinity/NaN 은 null 로 치환해서 반환.
    """
    row = (
        db.query(RobotData)
        .filter(RobotData.robot_name == robot_name)
        .order_by(RobotData.timestamp.desc())
        .first()
    )

    if not row:
        # 프론트에서 null 을 체크해서 "데이터 없음" 표시하도록 할 수 있음
        return None

    # scan_json 처리
    cleaned_scan: list[Optional[float]] = []
    try:
        if row.scan_json:
            raw_scan = json.loads(row.scan_json)
            cleaned_scan = [
                v if isinstance(v, (int, float)) and math.isfinite(v) else None
                for v in raw_scan
            ]
    except Exception:
        cleaned_scan = []

    # 프론트에서 쓰기 쉬운 dict 형태로 반환
    return {
        "robot_name": row.robot_name,
        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        "pos_x": row.pos_x,
        "pos_y": row.pos_y,
        "pos_z": row.pos_z,
        "orientation_yaw": row.orientation_yaw,
        "linear_velocity": row.linear_velocity,
        "angular_velocity": row.angular_velocity,
        "scan": cleaned_scan,
    }


# ---------- 2) 현재 상태 페이지(실시간 영상/정보) ----------

@router.get("/{robot_name}")
def robot_status_page(request: Request, robot_name: str):
    """
    현재 상태 페이지
    - /dashboard 에서 로봇을 클릭하면 이 페이지로 오는 대신,
      지금 설계에서는 /dashboard 안에서 탭으로 처리하므로
      이 페이지는 '직접 링크용' 정도로만 남겨둘 수도 있음.
    - 필요 없다면 안 써도 되고, 추후 확장용으로 유지해도 됨.
    """
    return templates.TemplateResponse(
        "robot_status.html",
        {"request": request, "robot_name": robot_name},
    )


# ---------- 3) 이동경로 페이지 ----------

@router.get("/{robot_name}/path")
def robot_path_page(request: Request, robot_name: str):
    """
    이동경로 페이지 (날짜/시간 입력 + 경로 시각화)
    """
    return templates.TemplateResponse(
        "robot_path.html",
        {"request": request, "robot_name": robot_name},
    )


# ---------- 4) 이동경로 데이터 API ----------

@router.get("/path/data")
def robot_path_data(
    robot_name: str,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    """
    특정 로봇의 이동경로 데이터를 반환.
    - [start, end] 구간의 pos_x, pos_y, timestamp 를 시간순으로 반환.
    """
    rows = (
        db.query(RobotData)
        .filter(RobotData.robot_name == robot_name)
        .filter(RobotData.timestamp >= start)
        .filter(RobotData.timestamp <= end)
        .order_by(RobotData.timestamp.asc())
        .all()
    )

    points = [
        {
            "x": r.pos_x,
            "y": r.pos_y,
            "t": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
        if r.pos_x is not None and r.pos_y is not None
    ]

    return {"robot_name": robot_name, "points": points}
