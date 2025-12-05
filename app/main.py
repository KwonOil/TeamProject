# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.database import Base, engine
from app.controllers.camera_controller import router as camera_router
from app.controllers.robot_controller import router as robot_router
from app.controllers.dashboard_controller import router as dashboard_router

app = FastAPI(title="Robot Dashboard")

Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(camera_router)
app.include_router(robot_router)
app.include_router(dashboard_router)

# 정적 파일
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# 메인 페이지('/')는 일단 비워두고, 대시보드로 들어가는 링크만 하나 둔다.
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
      <body style="font-family: Arial; padding: 20px;">
        <h2>Robot Dashboard</h2>
        <p><a href="/dashboard">대시보드로 이동</a></p>
      </body>
    </html>
    """
