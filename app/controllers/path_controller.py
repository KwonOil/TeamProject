# app/controllers/path_controller.py

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.robot_state_history import RobotStateHistory

# /path로 시작하는 URL들을 담당하는 라우터
router = APIRouter(prefix="/path", tags=["path"])

# 템플릿 엔진 (path.html에서 사용할 예정)
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def path_page(request: Request):
    """
    단순히 path.html을 렌더링하는 엔드포인트.
    - 필요 없다면 나중에 지워도 되지만,
      지금 구조에서는 유지해도 문제 없음.
    """
    return templates.TemplateResponse("path.html", {"request": request})


@router.get("/api/robot/{robot_name}/path")
def get_robot_path(
    robot_name: str,
    start: str,
    end: str,
    db: Session = Depends(get_db),
):
    """
    로봇의 이동 경로를 반환하는 API.

    - 프론트에서는 다음 형태로 호출:
      /path/api/robot/{robot_name}/path?start=YYYY-MM-DDTHH:MM:SS&end=...

      robot_path.js 기준:
        startFix = start + ":00"  # datetime-local 값 뒤에 ":00" 붙임
        endFix   = end   + ":00"
        fetch(`/path/api/robot/${robotName}/path?start=${startFix}&end=${endFix}`)

    - DB 테이블: RobotStateHistory
      * timestamp 컬럼 기준으로 구간 필터
      * pos_x, pos_y가 있는 것만 반환
    """

    # 문자열 → datetime 변환 (형식이 잘못되면 400 에러 응답)
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="start / end는 'YYYY-MM-DDTHH:MM:SS' 형식의 ISO datetime 이어야 합니다.",
        )

    # DB 조회: 특정 로봇 + 시간 구간
    rows = (
        db.query(RobotStateHistory)
        .filter(RobotStateHistory.robot_name == robot_name)
        .filter(RobotStateHistory.timestamp >= start_dt)
        .filter(RobotStateHistory.timestamp <= end_dt)
        .order_by(RobotStateHistory.timestamp.asc())
        .all()
    )

    # Chart.js의 data용 포인트 목록 생성
    points = []
    for r in rows:
        # 위치 정보 없는 레코드는 건너뜀
        if r.pos_x is None or r.pos_y is None or r.timestamp is None:
            continue

        points.append(
            {
                "x": r.pos_x,
                "y": r.pos_y,
                "t": r.timestamp.isoformat(),
            }
        )

    return {"points": points}
