# app/main.py
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config.database import Base, engine
from app.controllers.auth_controller import router as auth_router

from app.controllers.camera_controller import router as camera_router
from app.controllers.dashboard_controller import router as dashboard_router
from app.controllers.path_controller import router as path_router
from app.controllers.state_controller import router as state_router
from app.services.yolo_worker import yolo_worker
from app.services.state_history_worker import state_history_worker

from app.config.database_simulation import BaseSim, engine_sim
from app.controllers.simulation_controller import router as simulation_router
from app.services.simulation_history_worker import simulation_history_worker

from app.controllers.control_controller import router as control_router

app = FastAPI(title="Robot Dashboard")

# Base.metadata.create_all(bind=engine)
# BaseSim.metadata.create_all(bind=engine_sim)

# 세션 미들웨어 추가
# 실제 서비스에서는 환경변수 등으로 관리하는 것이 좋다.
app.add_middleware(
    SessionMiddleware,
    secret_key="MY_SECRET_KEY",
)

# 라우터 등록
app.include_router(auth_router)          # 로그인/로그아웃
app.include_router(camera_router)
app.include_router(state_router)
app.include_router(dashboard_router)
app.include_router(path_router)
app.include_router(control_router)
app.include_router(simulation_router)

# 정적 파일
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """
    루트 접근 시 기본적으로 /login 으로 리다이렉트한다.
    - 로그인 페이지에서 대시보드 / 시뮬레이션으로 이동.
    """
    return RedirectResponse(url="/login", status_code=302)


@app.on_event("startup")
async def startup_event():
    # 백그라운드 워커 실행
    asyncio.create_task(yolo_worker())
    asyncio.create_task(state_history_worker())
    asyncio.create_task(simulation_history_worker())
