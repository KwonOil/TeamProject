# app/services/simulation_service.py

from typing import List
from time import time

from sqlalchemy.orm import Session

from app.models.simulation_robot_data import SimulationRobotData

"""
시뮬레이션 로봇 관련 DB 조회 로직.

실제 로봇과 마찬가지로,
distinct 로봇 이름 목록 조회에 짧은 TTL 캐시를 둬서
시뮬레이션 대시보드 접근 시 DB 부하를 줄인다.
"""

_SIM_ROBOT_NAME_CACHE = {
    "data": [],        # type: List[str]
    "expires_at": 0.0,
}
_SIM_CACHE_TTL_SECONDS = 5.0


def get_distinct_sim_robot_names(db: Session) -> List[str]:
    """
    시뮬레이션 DB 에 저장된 로봇 이름 목록 조회.

    병목 완화:
    - dashboard 의 simulation 버전이 자주 열릴 때,
      매번 distinct 쿼리를 수행하지 않고 짧은 TTL 캐시를 재사용한다.
    """
    now = time()
    if now < _SIM_ROBOT_NAME_CACHE["expires_at"]:
        return _SIM_ROBOT_NAME_CACHE["data"]

    rows = (
        db.query(SimulationRobotData.robot_name)
        .distinct()
        .order_by(SimulationRobotData.robot_name)
        .all()
    )
    names = [r[0] for r in rows]

    _SIM_ROBOT_NAME_CACHE["data"] = names
    _SIM_ROBOT_NAME_CACHE["expires_at"] = now + _SIM_CACHE_TTL_SECONDS
    return names
