"""로봇 상태/이미지를 메모리에 보관하는 간단한 서비스."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class RobotStateManager:
    """여러 로봇의 최신 상태를 추적하는 in-memory 관리자."""

    def __init__(self) -> None:
        self._states: Dict[str, Dict[str, Any]] = {}
        self._images: Dict[str, bytes] = {}
        self._goals: Dict[str, Dict[str, Any]] = {}

    def update_state(self, robot_id: str, state_payload: Dict[str, Any]) -> Dict[str, Any]:
        """상태를 저장하고 타임스탬프를 덧붙여 반환."""

        payload = state_payload.copy()
        payload["robot_id"] = robot_id
        payload["last_updated"] = datetime.now(timezone.utc)
        self._states[robot_id] = payload
        return payload

    def get_state(self, robot_id: str) -> Optional[Dict[str, Any]]:
        """특정 로봇의 최신 상태를 조회."""

        return self._states.get(robot_id)

    def list_states(self) -> List[Dict[str, Any]]:
        """저장된 모든 로봇 상태를 반환."""

        return list(self._states.values())

    def store_image(self, robot_id: str, image_bytes: bytes) -> Dict[str, Any]:
        """최신 이미지를 저장하고 간단한 메타데이터를 반환."""

        self._images[robot_id] = image_bytes
        return {
            "robot_id": robot_id,
            "size_bytes": len(image_bytes),
            "stored_at": datetime.now(timezone.utc),
        }

    def get_image(self, robot_id: str) -> Optional[bytes]:
        """마지막으로 저장된 이미지를 조회."""

        return self._images.get(robot_id)

    def set_goal(self, robot_id: str, goal_payload: Dict[str, Any]) -> Dict[str, Any]:
        """목표 좌표를 임시 저장."""

        payload = {
            "robot_id": robot_id,
            "goal": goal_payload.copy(),
            "accepted_at": datetime.now(timezone.utc),
        }
        self._goals[robot_id] = payload
        return payload

    def get_goal(self, robot_id: str) -> Optional[Dict[str, Any]]:
        """마지막 목표 좌표를 조회."""

        return self._goals.get(robot_id)

