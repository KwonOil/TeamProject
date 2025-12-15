# app/controllers/map_controller.py

from fastapi import APIRouter, HTTPException
from app.services.map_service import load_map_info

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/info")
def get_map_info():
    """
    프론트(브라우저)가 맵을 그리기 위해 필요한 메타데이터를 제공.

    1단계에서 프론트는 이 정보를 받아서:
      - image_url을 로드해서 canvas 배경으로 그림
      - resolution, origin을 이용해 로봇 x,y를 픽셀로 변환해 점을 찍음
    """
    try:
        return load_map_info()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
