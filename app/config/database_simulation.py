# app/config/database_simulation.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

"""
시뮬레이션 전용 DB (simulation_robot_data 등)를 위한 설정.

실제 로봇 DB 와는 별도의 DB 를 사용한다고 가정.
"""

DEFAULT_SIM_DB_URL = "mysql+pymysql://oil:5151@100.90.191.42:3306/simulation"
SIM_DATABASE_URL = os.getenv("SIM_DATABASE_URL", DEFAULT_SIM_DB_URL)

engine_sim = create_engine(
    SIM_DATABASE_URL,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocalSim = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_sim,
)

BaseSim = declarative_base()


def get_sim_db():
    """
    시뮬레이션 DB용 Depends 함수.
    """
    db = SessionLocalSim()
    try:
        yield db
    finally:
        db.close()
