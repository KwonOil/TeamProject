# app/controllers/control_controller.py

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Request,
    HTTPException,
    Depends,
    Query,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.models.robot_state_history import RobotStateHistory
from app.models.user import User
from app.controllers.auth_controller import get_current_user

from app.services.control_service import (
    register_robot_control_ws,
    unregister_robot_control_ws,
    send_control_command,
)

router = APIRouter(prefix="/control", tags=["control"])
templates = Jinja2Templates(directory="app/templates")


# ==========================================================
# DB 세션 의존성
# ==========================================================
def get_db():
    """
    실제 로봇 DB 세션.
    controller 레이어에서만 사용.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# ✅ 이동 좌표 테이블 (여기만 수정하면 됨)
# ==========================================================
WAYPOINTS = {
    # 대기 장소
    "wait": {"x": 0.5, "y": 0.0, "yaw": 0.0},

    # 입구
    "entrance_1": {"x": 1.5, "y": 0.0, "yaw": 0.0},
    "entrance_2": {"x": 3.0, "y": 0.0, "yaw": 0.0},
    "entrance_3": {"x": 4.5, "y": 0.0, "yaw": 0.0},

    # 출구
    "exit_1": {"x": 1.5, "y": 1.0, "yaw": 0.0},
    "exit_2": {"x": 3.0, "y": 1.0, "yaw": 0.0},
    "exit_3": {"x": 4.5, "y": 1.0, "yaw": 0.0},
}


# ==========================================================
# 1) 로봇 조작 페이지 (GET)
#    /control?robot=tb3_1
# ==========================================================
@router.get("", response_class=HTMLResponse, response_model=None)
def control_page(
    request: Request,
    robot: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    로봇 조작 UI 페이지.

    - 로그인 필수
    - 왼쪽 로봇 탭 목록: robot_state_history 기준
    - ?robot=tb3_1 로 초기 선택 가능
    """

    # ✅ 로그인 체크
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # DB에 존재하는 로봇 목록
    rows = (
        db.query(RobotStateHistory.robot_name)
        .distinct()
        .order_by(RobotStateHistory.robot_name.asc())
        .all()
    )
    robot_names = [r[0] for r in rows]

    # 초기 선택 로봇 결정
    if robot and robot in robot_names:
        initial_robot = robot
    else:
        initial_robot = robot_names[0] if robot_names else ""

    return templates.TemplateResponse(
        "control.html",
        {
            "request": request,
            "robot_names": robot_names,
            "initial_robot": initial_robot,
            "user": user,
        },
    )


# ==========================================================
# 2) 대시보드 → 서버 : 이동 명령 API
#    POST /control/api/{robot_name}/goto?target=wait
# ==========================================================
@router.post("/api/{robot_name}/goto")
async def api_goto(
    robot_name: str,
    target: str = Query(..., description="이동할 목표 이름"),
    user: User = Depends(get_current_user),
):
    """
    지정된 로봇에게 Nav2 이동 명령을 전송한다.

    - 로그인 필수
    - target 은 WAYPOINTS 키여야 함
    - 실제 전송은 control_service 가 담당
    """

    # ✅ 로그인 확인
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # ✅ 좌표 존재 여부 확인
    if target not in WAYPOINTS:
        raise HTTPException(status_code=400, detail="Unknown target")

    pose = WAYPOINTS[target]

    command = {
        "type": "nav_goal",
        "target": target,
        "pose": pose,
        "requested_by": user.username,
    }

    # ✅ 로봇 WebSocket으로 명령 전송
    ok = await send_control_command(robot_name, command)
    if not ok:
        raise HTTPException(status_code=503, detail="Robot not connected")

    return {
        "status": "ok",
        "robot": robot_name,
        "target": target,
    }


# ==========================================================
# 3) 실제 로봇 → 서버 : 제어 WebSocket
#    ws://host/control/ws/robot/{robot_name}
# ==========================================================
@router.websocket("/ws/robot/{robot_name}")
async def robot_control_ws(websocket: WebSocket, robot_name: str):
    """
    실제 로봇이 접속하는 제어 WebSocket.

    - 서버 → 로봇 : nav_goal JSON 전송
    - 로봇 → 서버 : currently unused (heartbeat 용)
    """
    await websocket.accept()
    await register_robot_control_ws(robot_name, websocket)
    print(f"[CONTROL][WS][ROBOT] connected {robot_name}")

    try:
        while True:
            msg = await websocket.receive()
            if msg["type"] == "websocket.disconnect":
                break
            # 현재는 payload 사용 안 함
    finally:
        await unregister_robot_control_ws(robot_name, websocket)
        print(f"[CONTROL][WS][ROBOT] disconnected {robot_name}")
