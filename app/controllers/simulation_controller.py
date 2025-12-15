# app/controllers/simulation_controller.py

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config.database_simulation import get_sim_db
from app.services.simulation_service import get_distinct_sim_robot_names

router = APIRouter(tags=["simulation"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/simulation", response_class=HTMLResponse, response_model=None)
def simulation_dashboard(request: Request, db: Session = Depends(get_sim_db)):
    """
    시뮬레이션 대시보드 페이지.
    - 로그인 필요.
    - 시뮬레이션 DB에서 로봇 목록을 읽어와 왼쪽 탭을 구성한다.
    - 자주 호출되는 목록 조회는 simulation_service 의
      get_distinct_sim_robot_names 를 통해 캐시를 사용한다.
    """
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=303)

    robot_list = get_distinct_sim_robot_names(db)

    return templates.TemplateResponse(
        "simulation.html",
        {
            "request": request,
            "robot_names": robot_list,  # 템플릿에서 robot_names 사용하므로 이름 통일
            "initial_robot": robot_list[0] if robot_list else None,
        },
    )
