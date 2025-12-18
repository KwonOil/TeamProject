# app/services/state_history_queue.py
# 상태 히스토리 저장용 큐
import asyncio

# DB 저장용 비동기 큐
# - WebSocket 수신과 DB I/O 분리
# - 큐가 가득 차면 enqueue 쪽에서 제어
state_history_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
