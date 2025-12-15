# app/controllers/dashboard_controller.py

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.robot_state_history import RobotStateHistory
from app.controllers.auth_controller import get_current_user
from app.models.user import User

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(request: Request,
              db: Session = Depends(get_db),
              user: User | None = Depends(get_current_user)):
   # 로그인 체크
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    robot_names = (
        db.query(RobotStateHistory.robot_name)
        .distinct()
        .order_by(RobotStateHistory.robot_name)
        .all()
    )
    robot_names = [r[0] for r in robot_names]

    selected_robot = robot_names[0] if robot_names else None


    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "robot_names": robot_names,
            "selected_robot": selected_robot,
        },
    )
