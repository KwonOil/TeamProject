"""YOLO 추론 관련 REST 라우터."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from ..schemas.yolo import YOLOInferenceResponse
from ..services.yolo_service import YOLOService

router = APIRouter(prefix="/api/yolo", tags=["yolo"])


def get_yolo_service(request: Request) -> YOLOService:
    """앱 전역 상태에서 YOLOService 인스턴스를 꺼낸다."""

    service: YOLOService = request.app.state.yolo_service
    return service


@router.post("/inference", response_model=YOLOInferenceResponse)
async def run_yolo_inference(
    image: UploadFile = File(..., description="YOLO 분석 대상 프레임"),
    robot_id: str | None = None,
    yolo_service: YOLOService = Depends(get_yolo_service),
) -> YOLOInferenceResponse:
    """AI 팀이 제공한 YOLO 모델을 호출해 결과를 반환."""

    if image.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JPEG/PNG 이미지 파일만 허용됩니다.",
        )

    payload = await image.read()
    result = await yolo_service.run_inference(payload, robot_id)
    return YOLOInferenceResponse(**result)
