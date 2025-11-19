"""로봇 관련 Pydantic 스키마 정의 모듈."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Position(BaseModel):
    """지도 상의 로봇 위치를 표현하는 기본 구조체."""

    x: float = Field(..., description="지도 좌표계 X 값")
    y: float = Field(..., description="지도 좌표계 Y 값")
    theta: float = Field(..., description="yaw(heading) 값")


class RobotStatePayload(BaseModel):
    """로봇이 서버에 주기적으로 보고하는 상태 정보."""

    position: Position
    battery: float = Field(..., ge=0, le=100, description="배터리 잔량(%)")
    velocity: float = Field(..., description="로봇 속도 (m/s)")
    timestamp: Optional[int] = Field(
        default=None, description="ROS2 또는 시스템 타임스탬프 (epoch)"
    )


class RobotStateResponse(BaseModel):
    """상태 저장 이후 대시보드/로봇에 회신할 데이터."""

    robot_id: str
    position: Position
    battery: float
    velocity: float
    timestamp: Optional[int]
    last_updated: datetime


class RobotGoalPayload(BaseModel):
    """대시보드에서 요청하는 목표 좌표."""

    x: float
    y: float
    theta: float


class RobotGoalResponse(BaseModel):
    """목표 좌표 수신 결과 응답."""

    robot_id: str
    goal: RobotGoalPayload
    accepted_at: datetime
    message: str


class RobotImageResponse(BaseModel):
    """이미지 업로드 결과."""

    robot_id: str
    size_bytes: int
    stored_at: datetime
    note: str

