"""로봇 상태/이미지/목표 관련 REST 라우터."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from ..schemas.robot import (
    RobotGoalPayload,
    RobotGoalResponse,
    RobotImageResponse,
    RobotStatePayload,
    RobotStateResponse,
)
from ..services.robot_state_manager import RobotStateManager
from ..services.websocket_manager import WebSocketManager

router = APIRouter(prefix="/api/robots", tags=["robots"])


def get_state_manager(request: Request) -> RobotStateManager:
    """FastAPI app.state 에 등록된 RobotStateManager 를 주입."""

    manager: RobotStateManager = request.app.state.robot_state_manager
    return manager


def get_ws_manager(request: Request) -> WebSocketManager:
    """FastAPI app.state 에 등록된 WebSocketManager 를 주입."""

    manager: WebSocketManager = request.app.state.websocket_manager
    return manager


@router.post("/{robot_id}/state", response_model=RobotStateResponse)
@router.post("/{robot_id}/stat", response_model=RobotStateResponse)
async def update_robot_state(
    robot_id: str,
    payload: RobotStatePayload,
    state_manager: RobotStateManager = Depends(get_state_manager),
    ws_manager: WebSocketManager = Depends(get_ws_manager),
) -> RobotStateResponse:
    """로봇에서 올라오는 상태를 저장하고 대시보드에 브로드캐스트."""

    saved_state = state_manager.update_state(robot_id, payload.model_dump())
    await ws_manager.broadcast_state(saved_state)
    return RobotStateResponse(**saved_state)


@router.get("/{robot_id}/state", response_model=RobotStateResponse)
async def get_robot_state(
    robot_id: str,
    state_manager: RobotStateManager = Depends(get_state_manager),
) -> RobotStateResponse:
    """대시보드가 요청할 때 최신 상태를 반환."""

    state = state_manager.get_state(robot_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="상태가 없습니다.")
    return RobotStateResponse(**state)


@router.post("/{robot_id}/image", response_model=RobotImageResponse)
async def upload_robot_image(
    robot_id: str,
    image: UploadFile = File(..., description="JPEG 스트림"),
    state_manager: RobotStateManager = Depends(get_state_manager),
    ws_manager: WebSocketManager = Depends(get_ws_manager),
) -> RobotImageResponse:
    """로봇 카메라 프레임을 임시 저장하고 WebSocket 으로 전달."""

    if image.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JPEG/PNG 파일만 업로드 가능합니다.",
        )

    data = await image.read()
    meta = state_manager.store_image(robot_id, data)
    await ws_manager.broadcast_camera(robot_id, data)
    return RobotImageResponse(**meta, note="이미지 수신 완료")


@router.post("/{robot_id}/set_goal", response_model=RobotGoalResponse)
async def set_robot_goal(
    robot_id: str,
    payload: RobotGoalPayload,
    state_manager: RobotStateManager = Depends(get_state_manager),
) -> RobotGoalResponse:
    """대시보드/운용자가 요청한 목표 좌표를 저장."""

    saved_goal = state_manager.set_goal(robot_id, payload.model_dump())
    return RobotGoalResponse(
        robot_id=robot_id,
        goal=RobotGoalPayload(**saved_goal["goal"]),
        accepted_at=saved_goal["accepted_at"],
        message="Goal registered. 로봇팀에게 전달하세요.",
    )


@router.get("/{robot_id}/goal", response_model=RobotGoalResponse)
async def get_robot_goal(
    robot_id: str,
    state_manager: RobotStateManager = Depends(get_state_manager),
) -> RobotGoalResponse:
    """최근 저장된 목표 좌표를 조회."""

    goal = state_manager.get_goal(robot_id)
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="목표 정보가 없습니다.")
    return RobotGoalResponse(
        robot_id=robot_id,
        goal=RobotGoalPayload(**goal["goal"]),
        accepted_at=goal["accepted_at"],
        message="최근 목표 좌표를 반환합니다.",
    )

