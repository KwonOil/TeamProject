# app/services/map_service.py

import os
import re
import ast
from typing import Any, Dict, Tuple


# ------------------------------------------------------------
# 맵 설정 파일 경로
# - 필요하면 환경변수로 바꿀 수 있게 해둠
# ------------------------------------------------------------
DEFAULT_MAP_YAML_PATH = os.getenv("MAP_YAML_PATH", "app/static/maps/airport_map.yaml")


def _parse_yaml_value(line: str) -> Tuple[str, str] | None:
    """
    매우 단순한 YAML key: value 파서.
    - airport_map.yaml은 구조가 단순하기 때문에 PyYAML 없이도 1단계는 충분히 처리 가능
    - 복잡한 YAML이면 PyYAML을 쓰는 게 맞지만, 지금은 병목/의존성 최소화가 목적

    예)
      image: airport_map.png
      resolution: 0.05
      origin: [-10.0, -10.0, 0.0]
    """
    line = line.strip()

    # 주석/빈 줄 무시
    if not line or line.startswith("#"):
        return None

    # key: value 형태만 처리
    m = re.match(r"^([A-Za-z_]+)\s*:\s*(.+)$", line)
    if not m:
        return None

    key = m.group(1).strip()
    value = m.group(2).strip()
    return key, value


def load_map_info(yaml_path: str = DEFAULT_MAP_YAML_PATH) -> Dict[str, Any]:
    """
    airport_map.yaml을 읽어 웹에서 필요한 정보만 추출해 반환한다.

    반환 예:
    {
      "image_url": "/static/maps/airport_map.png",
      "resolution": 0.05,
      "origin": [-10.0, -10.0, 0.0]
    }

    주의:
    - origin은 보통 [x, y, yaw] 형태다.
    - 1단계에서는 yaw는 사용하지 않고 x,y만 사용한다.
    """
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"map yaml not found: {yaml_path}")

    image = None
    resolution = None
    origin = None

    with open(yaml_path, "r", encoding="utf-8") as f:
        for raw in f:
            parsed = _parse_yaml_value(raw)
            if not parsed:
                continue

            key, value = parsed

            if key == "image":
                # image: airport_map.png 또는 image: airport_map.pgm 같은 값
                # yaml이 상대경로를 쓰는 경우가 많으므로 파일명만 추출
                image = value.strip().strip('"').strip("'")

            elif key == "resolution":
                # resolution: 0.05
                try:
                    resolution = float(value)
                except ValueError:
                    pass

            elif key == "origin":
                # origin: [-10.0, -10.0, 0.0]
                # YAML 리스트는 Python literal과 유사하므로 ast.literal_eval로 안전 파싱
                try:
                    origin = ast.literal_eval(value)
                except Exception:
                    pass

    if image is None or resolution is None or origin is None:
        raise ValueError(
            f"invalid airport_map.yaml (need image/resolution/origin). "
            f"parsed=image({image}) resolution({resolution}) origin({origin})"
        )

    # ------------------------------------------------------------
    # image 파일을 /static 경로로 제공하기 위한 URL 생성
    # - 우리는 app/static/maps/ 아래에 파일을 두기로 했음
    # - yaml의 image가 상대경로("airport_map.png")일 때를 기준으로 처리
    # ------------------------------------------------------------
    image_filename = os.path.basename(image)
    image_url = f"/static/maps/{image_filename}"

    return {
        "image_url": image_url,
        "resolution": resolution,
        "origin": origin,
    }
