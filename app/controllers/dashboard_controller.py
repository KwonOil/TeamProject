# app/controllers/dashboard_controller.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.models.robot_state_history import RobotStateHistory
from app.config.database import get_db

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse, response_model=None)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    실제 로봇 대시보드 페이지.
    - 반드시 로그인 되어 있어야 접근 가능.
    - 로그인은 SessionMiddleware를 통해 request.session에서 확인한다.
    """
    if not request.session.get("user_id"):
        # 로그인 안 되어 있으면 /login 으로 보냄
        return RedirectResponse(url="/login", status_code=303)

    # 로봇 이름만 중복 없이 가져오기
    robot_names = (
        db.query(RobotStateHistory.robot_name)
        .distinct()
        .order_by(RobotStateHistory.robot_name)
        .all()
    )
    robot_names = [r[0] for r in robot_names]

    initial_robot = robot_names[0] if robot_names else None

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "robot_names": robot_names,
            "initial_robot": initial_robot,
        },
    )
