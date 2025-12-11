# app/services/state_history_service.py
from app.services.state_service import state_history_queue

async def enqueue_state_history(robot_name: str, data: dict):
    """
    상태 메시지를 DB 저장용 큐로 전달
    DB 작업은 worker가 처리하므로 여기서는 큐에 넣기만 한다
    """
    await state_history_queue.put({
        "robot_name": robot_name,
        "data": data
    })
