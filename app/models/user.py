# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
from app.config.database import Base

class User(Base):
    """
    DB 관리자가 만들어둔 users 테이블과 매핑되는 SQLAlchemy 모델.
    - 테이블 생성/삭제를 위해 쓰는 것이 아니라
      SELECT로 조회할 때만 사용한다.
    - 컬럼 정의는 실제 테이블 구조와 일치해야 한다.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # 예: "admin", "user"
    role = Column(String(20), nullable=False, default="user")

    # 비활성 계정 처리용 플래그
    is_active = Column(Boolean, nullable=False, default=True)

     # ✅ DB가 자동으로 관리하게 맡긴다
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )