"""YOLO 추론을 FastAPI에서 호출하기 위한 간단한 서비스."""
from __future__ import annotations

import asyncio
import base64
from typing import Any, Dict, List, Optional


class YOLOService:
    """YOLOv8 추론 호출을 감싸는 헬퍼 클래스."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        # 실제 프로젝트에서는 best.pt 등의 모델 경로를 전달하면 된다.
        self.model_path = model_path or "best.pt"
        self._model = None
        self._model_load_error: Optional[Exception] = None

    def _load_model_if_possible(self) -> None:
        """ultralytics 가 설치된 경우에만 모델을 불러온다."""

        if self._model is not None or self._model_load_error is not None:
            return
        try:
            from ultralytics import YOLO  # type: ignore
        except Exception as exc:  # pragma: no cover - 선택적 의존성
            # 로컬 환경에서 ultralytics 가 없더라도 서버가 동작하도록 예외를 저장만 한다.
            self._model_load_error = exc
            return
        self._model = YOLO(self.model_path)

    def _predict_sync(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """스레드 풀에서 실행될 동기 추론 함수."""

        if self._model is None:
            return []
        results = self._model(image_bytes)[0]
        detections: List[Dict[str, Any]] = []
        for box in results.boxes:
            cls_id = int(box.cls[0]) if box.cls is not None else -1
            confidence = float(box.conf[0]) if box.conf is not None else 0.0
            label = results.names.get(cls_id, f"class_{cls_id}")
            detections.append({"class": label, "confidence": confidence})
        return detections

    async def run_inference(
        self, image_bytes: bytes, robot_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """이미지를 받아 YOLO 추론 결과와 base64 이미지를 반환."""

        self._load_model_if_possible()
        encoded = base64.b64encode(image_bytes).decode("ascii")

        objects: List[Dict[str, Any]]
        if self._model is None:
            # ultralytics 가 설치되지 않은 개발 환경을 고려한 기본 응답
            objects = [{"class": "unknown", "confidence": 0.0}]
        else:
            loop = asyncio.get_running_loop()
            objects = await loop.run_in_executor(
                None, self._predict_sync, image_bytes
            )

        return {
            "robot_id": robot_id,
            "objects": objects,
            "image_base64": encoded,
        }
