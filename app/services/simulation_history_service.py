# app/services/simulation_history_service.py
import asyncio

simulation_history_queue: asyncio.Queue = asyncio.Queue(maxsize=2000)

async def enqueue_simulation_history(robot_name: str, data: dict):
    await simulation_history_queue.put({
        "robot_name": robot_name,
        "data": data
    })
