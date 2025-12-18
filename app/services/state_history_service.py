# app/services/state_history_service.py
# WebSocket 수신부 → DB 저장 큐 전달
from app.services.state_history_queue import state_history_queue

async def enqueue_state_history(robot_name: str, data: dict):
    """
    상태 메시지를 DB 저장 큐로 전달

    - 여기서는 DB 작업을 하지 않는다
    - 최대한 가볍게 유지해야 한다
    """

    await state_history_queue.put({
        "robot_name": robot_name,
        "data": data,
    })
