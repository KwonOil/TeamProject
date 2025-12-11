# app/config/database_simulation.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "mysql+pymysql://oil:5151@100.90.191.42:3306/simulation"

engine_sim = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

SessionLocalSim = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_sim,
)

BaseSim = declarative_base()
