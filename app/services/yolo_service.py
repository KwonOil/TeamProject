# app/services/yolo_service.py

import httpx
from typing import List, Dict, Any

# ✅ YOLO 추론 서버 주소
YOLO_SERVER_URL = "http://100.117.55.65:8001/infer"


async def run_yolo_infer(image_bytes: bytes) -> List[Dict[str, Any]]:
    """
    YOLO 서버에 이미지를 비동기로 보내어 추론 결과를 받는다.

    - httpx.AsyncClient 사용
    - 이벤트 루프를 절대 블로킹하지 않음
    """

    # YOLO 서버가 느리거나 끊겨도
    # 메인 서버 전체가 멈추지 않도록 timeout 명시
    timeout = httpx.Timeout(
        connect=1.0,
        read=1.0,
        write=1.0,
        pool=1.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            print("[YOLO][REQ] sending image", len(image_bytes))

            response = await client.post(
                YOLO_SERVER_URL,
                files={
                    # FastAPI UploadFile 호환 형식
                    "file": ("frame.jpg", image_bytes, "image/jpeg")
                },
            )

            print("[YOLO][RESP] status", response.status_code)

            # HTTP 에러 처리
            response.raise_for_status()

            # YOLO 서버는 JSON 반환한다고 가정
            return response.json()

    except httpx.TimeoutException:
        print("[YOLO][TIMEOUT] YOLO server timeout")
        return []

    except httpx.HTTPError as e:
        print("[YOLO][HTTP ERROR]", str(e))
        return []

    except Exception as e:
        print("[YOLO][ERROR]", str(e))
        return []
