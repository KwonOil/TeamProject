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