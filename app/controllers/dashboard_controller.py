# app/controllers/dashboard_controller.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.robot_data import RobotData

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    대시보드 메인 페이지
    - DB에서 robot_name 목록을 읽어와서 탭으로 표시
    - 실제 상태 데이터는 JS가 /robot/status 를 주기적으로 호출
    """
    rows = (
        db.query(RobotData.robot_name)
        .distinct()
        .order_by(RobotData.robot_name.asc())
        .all()
    )
    robot_names = [r[0] for r in rows]

    # 로봇이 하나도 없을 수도 있으니 기본 선택값은 조건부로 처리
    initial_robot = robot_names[0] if robot_names else ""

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "robot_names": robot_names,
            "initial_robot": initial_robot,
        },
    )
