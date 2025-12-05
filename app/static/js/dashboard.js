// app/static/dashboard.js

// 현재 선택된 로봇 이름 (서버에서 넘어온 초기값 사용)
let currentRobot = window.INITIAL_ROBOT_NAME || "";
let ws = null;  // 카메라 WebSocket

// -------------------- WebSocket (카메라 영상) --------------------

function openCameraWebSocket() {
    if (!currentRobot) {
        console.log("선택된 로봇이 없습니다. WebSocket 연결 생략.");
        return;
    }

    // 기존 연결이 있다면 정리
    if (ws) {
        ws.close();
        ws = null;
    }

    const url = `ws://${location.host}/camera/ws/${currentRobot}`;
    ws = new WebSocket(url);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
        console.log("WS connected for", currentRobot);
    };

    ws.onmessage = (e) => {
        // 수신된 바이너리를 이미지로 변환해서 <img>에 표시
        const blob = new Blob([e.data], { type: "image/jpeg" });
        document.getElementById("cam").src = URL.createObjectURL(blob);
    };

    ws.onclose = () => {
        console.log("WS closed");
    };

    ws.onerror = (err) => {
        console.error("WS error:", err);
    };
}

// -------------------- 로봇 상태 주기 업데이트 --------------------

async function updateStatus() {
    if (!currentRobot) return;

    try {
        const res = await fetch(`/robot/status?robot_name=${currentRobot}`);
        if (!res.ok) {
            console.error("status fetch error", res.status);
            return;
        }
        const data = await res.json();
        if (!data) {
            // DB에 데이터가 아직 없을 때
            document.getElementById("posText").textContent = "데이터 없음";
            return;
        }

        // 위치 / 속도 / 각속도 / yaw
        const x = data.pos_x ?? 0;
        const y = data.pos_y ?? 0;
        const v = data.linear_velocity ?? 0;
        const av = data.angular_velocity ?? 0;
        const yawRad = data.orientation_yaw ?? 0;
        const yawDeg = yawRad * 180.0 / Math.PI;

        document.getElementById("posText").textContent = `${x.toFixed(2)} , ${y.toFixed(2)}`;
        document.getElementById("velText").textContent = v.toFixed(2);
        document.getElementById("angVelText").textContent = av.toFixed(2);
        document.getElementById("yawText").textContent = yawDeg.toFixed(1);

        // 배터리는 나중에 DB/토픽에서 가져와 붙이면 됨. 일단은 placeholder.
        document.getElementById("batteryText").textContent = "DB 연동 예정";

        // 타임스탬프
        if (data.timestamp) {
            document.getElementById("timestampText").textContent = data.timestamp;
        }

        // 센서(LaserScan) 일부를 표에 표시
        const scan = data.scan || [];
        const body = document.getElementById("sensorBody");
        body.innerHTML = "";

        const limit = Math.min(scan.length, 30);  // 30개만 표시
        for (let i = 0; i < limit; i++) {
            const row = document.createElement("tr");

            const cIdx = document.createElement("td");
            cIdx.textContent = i;

            const cVal = document.createElement("td");
            const v = scan[i];
            cVal.textContent = v === null ? "N/A" : v.toFixed(3);

            row.appendChild(cIdx);
            row.appendChild(cVal);
            body.appendChild(row);
        }
    } catch (e) {
        console.error("updateStatus error", e);
    }
}

// 1초마다 상태 갱신
setInterval(updateStatus, 1000);

// -------------------- 로봇 탭 클릭 처리 --------------------

function initRobotTabs() {
    const tabs = document.querySelectorAll(".robot-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const name = tab.getAttribute("data-robot");
            if (!name) return;

            currentRobot = name;
            document.getElementById("currentRobotName").textContent = currentRobot;

            // 탭 스타일 업데이트
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            // 카메라 WebSocket 재연결
            openCameraWebSocket();

            // 상태 즉시 한 번 갱신
            updateStatus();
        });
    });
}

// -------------------- 이동경로 버튼 --------------------

function initMovePathButton() {
    const btn = document.getElementById("movePathBtn");
    btn.addEventListener("click", () => {
        if (!currentRobot) return;
        // 해당 로봇의 이동경로 페이지로 이동
        window.location.href = `/robot/${currentRobot}/path`;
    });
}

// -------------------- 초기화 --------------------

window.addEventListener("DOMContentLoaded", () => {
    initRobotTabs();
    initMovePathButton();
    if (currentRobot) {
        openCameraWebSocket();
        updateStatus();
    }
});
