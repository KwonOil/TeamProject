# app/services/robot_service.py

from typing import List
from time import time

from sqlalchemy.orm import Session

from app.models.robot_state_history import RobotStateHistory

"""
로봇 관련 DB 조회 로직.

병목 개선 포인트:
- get_latest_robot_data : 인덱스 + 정렬으로 "마지막 레코드 하나"만 빠르게 조회.
- get_distinct_robot_names : 자주 호출되는 로봇 목록 조회에
  짧은 TTL 기반 인메모리 캐시 적용.
"""

# 짧은 TTL(초 단위) 캐시
_ROBOT_NAME_CACHE = {
    "data": [],        # type: List[str]
    "expires_at": 0.0, # 유닉스 타임스탬프
}
_CACHE_TTL_SECONDS = 5.0  # 5초 정도면 새로고침에도 DB 부담이 확 줄어든다.


def get_latest_robot_data(db: Session, robot_name: str) -> RobotStateHistory | None:
    """
    특정 로봇의 "가장 최근 상태" 한 건을 가져온다.

    성능 팁:
    - RobotStateHistory 에 (robot_name, timestamp) 또는 (robot_name, id) 인덱스를 걸어두면
      ORDER BY + LIMIT 1 쿼리가 매우 빠르게 수행된다.
    """
    return (
        db.query(RobotStateHistory)
        .filter(RobotStateHistory.robot_name == robot_name)
        .order_by(RobotStateHistory.id.desc())  # id 가 AUTO_INCREMENT 라고 가정
        .first()
    )


def get_distinct_robot_names(db: Session) -> List[str]:
    """
    히스토리 테이블에서 중복 없이 로봇 이름 목록만 가져온다.

    병목 완화:
    - dashboard / control 페이지가 자주 열리면
      매번 distinct 쿼리가 히스토리 전체 테이블을 스캔할 수 있다.
    - 짧은 TTL(5초) 캐시를 두어 같은 이름 목록을 여러 번 재사용하면
      DB 부하가 크게 줄어든다.
    """
    now = time()
    if now < _ROBOT_NAME_CACHE["expires_at"]:
        # 캐시 유효기간 이내 → 메모리에서 반환
        return _ROBOT_NAME_CACHE["data"]

    rows = (
        db.query(RobotStateHistory.robot_name)
        .distinct()
        .order_by(RobotStateHistory.robot_name)
        .all()
    )
    names = [r[0] for r in rows]

    _ROBOT_NAME_CACHE["data"] = names
    _ROBOT_NAME_CACHE["expires_at"] = now + _CACHE_TTL_SECONDS
    return names
