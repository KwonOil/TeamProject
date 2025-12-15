# app/controllers/robot_state_controller.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["robot-state"])


@router.post("/select_robot")
async def select_robot(request: Request):
    """
    사이드바에서 선택한 로봇을 서버 세션에 저장한다.
    모든 페이지에서 공통으로 사용되는 상태.
    """
    data = await request.json()
    robot = data.get("robot")

    if robot:
        request.session["selected_robot"] = robot

    return JSONResponse({"status": "ok", "selected_robot": robot})
