# 🟦 **1. 로봇팀 문서 – Robot Team Guide**

**ROS2 Humble + Ubuntu 22.04 기반**

---

## 📌 1) 책임 범위

- SLAM 구축
- Navigation2 설정
- 로봇의 상태(state) publish
- 로봇이 서버 API에 주기적으로 데이터 전달
- 목표 좌표(goal) 수신 및 Nav2로 이동
- 장애물 회피 및 멀티 로봇 네임스페이스 구성

---

## 📌 2) ROS2 노드 구성도

```
/robot_X/
 ├── slam_toolbox
 ├── nav2 (bt_navigator, controller, planner, behavior_tree)
 ├── robot_state_publisher
 ├── camera_node
 ├── robot_status_node  → 서버 API로 상태 전송
 ├── goal_receiver_node → 서버가 전송한 목적지 수신
 └── tf2 (map → odom → base_link)
```

---

## 📌 3) 로봇 → 서버 통신 방식

FastAPI REST 엔드포인트:

```
POST /api/robots/{robot_id}/state
POST /api/robots/{robot_id}/image
```

전송 데이터 예:

```json
{
  "robot_id": "robot_1",
  "position": {"x": 1.2, "y": -0.4, "theta": 0.1},
  "battery": 89,
  "velocity": 0.24,
  "timestamp": 1712345123
}
```

카메라 프레임은 JPEG 바이트로 업로드.

---

## 📌 4) 서버 → 로봇 명령 흐름

대시보드 → FastAPI → 로봇:

```
POST /api/robots/{robot_id}/set_goal
```

예:

```json
{"x": 3.5, "y": -2.0, "theta": 0.0}
```

로봇팀은 이 goal을 `/navigate_to_pose` action으로 전달.

---

## 📌 5) 멀티 로봇 네임스페이스 기준

각 로봇은 다음 구조를 갖는다:

```
/robot1/...
/robot2/...
```

TF Tree:

```
/robot1/map
/robot1/odom
/robot1/base_link
```

# 🟪 2**. AI 팀 문서 – YOLOv8 Team Guide**

---

## 📌 1) 책임 범위

- 관리자/일반인 이미지 학습
- YOLOv8 backbone 선택
- best.pt 모델 제공
- inference 서비스 제공 (FastAPI 연동)
- 이벤트 감지 로직 제공

---

## 📌 2) 데이터 규칙

YOLOv5/YOLOv8 공통 포맷:

```
images/train
images/val
labels/train
labels/val
data.yaml
```

---

## 📌 3) 학습 명령 예

```bash
yolo train model=yolov8s.pt data=data.yaml epochs=100 imgsz=640
```

---

## 📌 4) inference 모듈

FastAPI에서 사용하기 위한 Python 코드:

```python
from ultralytics import YOLO

model = YOLO("best.pt")

def run_inference(frame):
    result = model(frame)[0]
    return result
```

---

## 📌 5) 이벤트 규칙 정의

예시:

- 사람이 탐지되면
    - `manager` → normal
    - `visitor` → warning
    - `unknown` → alert (대시보드 표시)

이 규칙은 서버팀과 공유.

# 🟧 3**. 서버·백엔드 팀 문서 – FastAPI Team Guide**

---

## 📌 1) 책임 범위

- FastAPI 서버 전체 구축
- REST API
- WebSocket 실시간 프레임 스트림
- YOLO inference 서버와 연결
- DB(MySQL)과 연동
- 멀티 로봇 상태 관리 (in-memory 또는 Redis)

---

## 📌 2) FastAPI 서버 아키텍처

```
/server
 ├── main.py
 ├── api/
 │    ├── robots.py
 │    ├── yolo.py
 │    ├── dashboard.py
 ├── services/
 │    ├── robot_state_manager.py
 │    ├── yolo_service.py
 │    ├── websocket_manager.py
 ├── db/
 │    └── mysql_connector.py
 ├── models/
 ├── schemas/
 └── static/
```

---

## 📌 3) 로봇 관련 API

### ● 상태 업데이트

```
POST /api/robots/{robot_id}/stat
```

### ● 이미지 업로드

```
POST /api/robots/{robot_id}/image
```

### ● 목적지 명령

```
POST /api/robots/{robot_id}/set_goal
```

---

## 📌 4) YOLO 분석 API

```
POST /api/yolo/inference
```

응답:

```json
{
  "objects": [
    {"class": "manager", "confidence": 0.91}
  ],
  "image_base64": "..."
}
```

---

## 📌 5) 대시보드 WebSocket

**실시간 상태 스트림**

```
WS /ws/robots/state
```

**실시간 카메라 스트림**

```
WS /ws/robots/{robot_id}/camera
```

서버는 로봇이 전송하는 이미지를

WebSocket을 통해 대시보드로 push.

---

## 📌 6) DB 설계

### robots 테이블

```
robot_id | x | y | theta | battery | last_update
```

### events 테이블

```
event_id | robot_id | event_type | timestamp | info
```

### inference_log

```
id | robot_id | class | confidence | timestamp
```

# 🟩 **4. 대시보드 팀 문서 – Dashboard (Frontend) Guide**

---

## 📌 1) 책임 범위

- 로봇 실시간 모니터링 UI
- 맵 + 경로 표시
- 로봇 선택 UI
- WebSocket 수신
- YOLO 분석 결과 아이콘 표시
- 관리자/일반인 식별

---

## 📌 2) 주요 API

### ● 상태 조회

```
GET /api/robots/{robot_id}/state
```

### ● WebSocket 실시간 수신

```
ws = new WebSocket("ws://SERVER/ws/robots/camera");
```

### ● 목적지 명령

```
POST /api/robots/{robot_id}/set_goal
```

---

## 📌 3) 실시간 영상 표시

```jsx
ws.onmessage = (msg) => {
    const image = document.getElementById("cam");
    image.src = "data:image/jpeg;base64," + msg.data;
};
```

---

## 📌 4) 실시간 지도 표시

- ROS2 map을 이미지로 변환해 서버가 제공
- 프론트는 Canvas로 로봇 위치 표시
- WebSocket 상태 업데이트로 좌표 갱신