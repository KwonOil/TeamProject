# app/config/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

"""
DB 연결/세션 관련 설정 파일.

핵심 포인트
- DATABASE_URL 은 환경변수로 관리 (코드에 계정/주소 하드코딩 X)
- connection pool 옵션 튜닝으로 과도한 커넥션 생성/종료를 줄여 병목 완화
- 웹 요청용 SessionLocal 과, 백그라운드 워커에서 사용할 동일 세션 팩토리 제공
"""

# ============================================================
# 1) DB URL 설정
#    - 실제 서비스에서는 .env / 환경변수에서 가져오는 것을 권장한다.
# ============================================================
DEFAULT_DB_URL = "mysql+pymysql://oil:5151@100.90.191.42:3306/teamproject"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# ============================================================
# 2) SQLAlchemy Engine 생성
#    - connection pool 설정으로 DB 커넥션 재사용 극대화
#    - pool_size / max_overflow / pool_recycle 등은
#      실제 서비스 환경에 맞게 조정 가능
# ============================================================
engine = create_engine(
    DATABASE_URL,
    echo=False,          # 개발 중 쿼리 로그 보고 싶으면 True
    future=True,         # 2.x 스타일 API
    pool_size=10,        # 동시에 유지할 기본 커넥션 수
    max_overflow=20,     # pool_size 를 초과해서 추가로 열 수 있는 커넥션 수
    pool_pre_ping=True,  # 커넥션이 죽었는지 체크하고 재연결
    pool_recycle=1800,   # 1800초(30분)마다 커넥션 재생성 (MySQL wait_timeout 회피)
)

# ============================================================
# 3) 세션 팩토리
#    - 웹 요청 / 백그라운드 워커에서 공통으로 사용
# ============================================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ============================================================
# 4) Base 클래스 (모든 모델이 상속)
# ============================================================
Base = declarative_base()


# ============================================================
# 5) FastAPI 의 Depends 에서 사용하는 세션 의존성
#    - 웹 요청 단위로 세션을 만들고, 요청이 끝나면 닫아준다.
# ============================================================
def get_db():
    """
    FastAPI 의 Depends 에서 사용되는 DB 세션 제공 함수.
    - 요청 하나 당 세션 1개를 생성/종료.
    - with 문 대신 try/finally 로 명시적으로 닫아준다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
