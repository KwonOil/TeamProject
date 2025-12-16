# app/services/state_history_service.py
from app.services.state_service import state_history_queue

async def enqueue_state_history(robot_name: str, data: dict):
    """
    WebSocket 수신부에서 호출
    - DB 작업은 하지 않는다
    - 큐에 그대로 밀어 넣는다
    """
    await state_history_queue.put({
        "robot_name": robot_name,
        "data": data
    })
