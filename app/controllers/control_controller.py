from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException,
    Query,
    WebSocket,
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.user import User
from app.controllers.auth_controller import get_current_user
from app.services.robot_service import get_distinct_robot_names
from app.services.control_service import (
    send_control_command,
    register_robot_control_ws,
    unregister_robot_control_ws,
)

router = APIRouter(prefix="/control", tags=["control"])
templates = Jinja2Templates(directory="app/templates")


# ==========================================================
# 이동 좌표 테이블
# ==========================================================
WAYPOINTS = {
    "wait": {"x": 0.39, "y": -0.03, "yaw": 0.0},

    "entrance_1": {"x": 0.02, "y": -0.66, "yaw": 0.0},
    "entrance_2": {"x": 0.02, "y": 0.04, "yaw": 0.0},
    "entrance_3": {"x": 0.02, "y": 0.66, "yaw": 0.0},
    
    "exit_1": {"x": 1.87, "y": -0.76, "yaw": 0.0},
    "exit_2": {"x": 1.87, "y": 0.02, "yaw": 0.0},
    "exit_3": {"x": 1.87, "y": 0.67, "yaw": 0.0},
}


# ==========================================================
# 1) 로봇 조작 페이지
# ==========================================================
@router.get("")
def control_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    robot_names = get_distinct_robot_names(db)

    selected_robot = request.session.get("selected_robot")
    if selected_robot not in robot_names:
        selected_robot = robot_names[0] if robot_names else None
        request.session["selected_robot"] = selected_robot

    return templates.TemplateResponse(
        "control.html",
        {
            "request": request,
            "robot_names": robot_names,
            "selected_robot": selected_robot,
            "user": user,
        },
    )


# ==========================================================
# 2) 이동 명령 API
# ==========================================================
@router.post("/api/{robot_name}/goto")
async def api_goto(
    robot_name: str,
    target: str = Query(...),
    user: User = Depends(get_current_user),
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if target not in WAYPOINTS:
        raise HTTPException(status_code=400, detail="Unknown target")

    command = {
        "type": "nav_goal",
        "target": target,
        "pose": WAYPOINTS[target],
        "requested_by": user.username,
    }

    ok = await send_control_command(robot_name, command)
    if not ok:
        raise HTTPException(status_code=503, detail="Robot not connected")

    return {"status": "ok"}


# ==========================================================
# 3) 실제 로봇 → 서버 : 제어 WebSocket
# ==========================================================
@router.websocket("/ws/robot/{robot_name}")
async def robot_control_ws(websocket: WebSocket, robot_name: str):
    """
    실제 로봇이 접속하는 제어 WebSocket.
    - 서버 → 로봇 : 이동 명령 전송
    """
    await websocket.accept()
    await register_robot_control_ws(robot_name, websocket)
    print(f"[ROBOT][CONTROL][WS] connected {robot_name}")

    try:
        while True:
            # 현재는 로봇 → 서버 메시지는 사용 안 함
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        await unregister_robot_control_ws(robot_name, websocket)
        print(f"[ROBOT][CONTROL][WS] disconnected {robot_name}")
