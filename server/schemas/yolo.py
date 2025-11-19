"""YOLO 추론 API를 위한 스키마."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class DetectionObject(BaseModel):
    """YOLO가 탐지한 물체 정보."""

    class_name: str = Field(..., alias="class", description="탐지된 클래스 이름")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도(0~1)")

    class Config:
        allow_population_by_field_name = True


class YOLOInferenceResponse(BaseModel):
    """YOLO 추론 결과 응답."""

    robot_id: Optional[str] = Field(
        default=None, description="해당 프레임을 전송한 로봇 식별자"
    )
    objects: List[DetectionObject]
    image_base64: str = Field(..., description="base64로 인코딩된 결과 이미지")

