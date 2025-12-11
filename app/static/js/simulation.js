// app/static/js/simulation.js
let currentRobot = window.INITIAL_ROBOT_NAME;
let camWs = null;
let stateWs = null;

window.addEventListener("DOMContentLoaded", () => {
    if (!currentRobot) {
        const firstTab = document.querySelector(".robot-tab");
        if (firstTab) {
            currentRobot = firstTab.dataset.robot;
            document.getElementById("currentRobotName").textContent = currentRobot;
        }
    }

    if (currentRobot) {
        openCameraWS();
        openStateWS();
    }
});

/* =========================
   YOLO 박스 그리기
========================= */
function drawDetections(detections) {
    if (!Array.isArray(detections)) return;

    const canvas = document.getElementById("overlay");
    const ctx = canvas.getContext("2d");

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = "red";
    ctx.fillStyle = "red";
    ctx.lineWidth = 2;
    ctx.font = "14px Arial";

    detections.forEach(det => {
        const [x1, y1, x2, y2] = det.bbox;
        const w = x2 - x1;
        const h = y2 - y1;

        ctx.strokeRect(x1, y1, w, h);

        const label = `${det.class} ${(det.conf * 100).toFixed(1)}%`;
        const textWidth = ctx.measureText(label).width;

        ctx.fillRect(x1, y1 - 18, textWidth + 6, 16);
        ctx.fillStyle = "white";
        ctx.fillText(label, x1 + 3, y1 - 5);
        ctx.fillStyle = "red";
    });
}

/* =========================
   Camera WebSocket
========================= */
function openCameraWS() {
    if (camWs) camWs.close();

    const url = `ws://${location.host}/camera/view/sim/${currentRobot}`;
    console.log("[CAMERA][WS]", url);

    camWs = new WebSocket(url);
    camWs.binaryType = "arraybuffer";

    camWs.onmessage = e => {
        if (e.data instanceof ArrayBuffer) {
            const blob = new Blob([e.data], { type: "image/jpeg" });
            document.getElementById("cam").src =
                URL.createObjectURL(blob);
            return;
        }

        try {
            const msg = JSON.parse(e.data);
            if (msg.type === "yolo") {
                const dets = Array.isArray(msg.detections)
                    ? msg.detections
                    : msg.detections?.detections;
                drawDetections(dets);
            }
        } catch (_) {}
    };
}

/* =========================
   State WebSocket
========================= */
function openStateWS() {
    if (stateWs) stateWs.close();

    const url = `ws://${location.host}/state/view/sim/${currentRobot}`;
    console.log("[STATE][WS]", url);

    stateWs = new WebSocket(url);
    stateWs.onmessage = e => {
        try {
            const msg = JSON.parse(e.data);
            console.log("stateWs msg : ",msg);
            handleState(msg);
        } catch (err) {
            console.error("[STATE][PARSE ERROR]", err, e.data);
        }
    };
}

/* =========================
   Small Value Clamp
========================= */
function clampSmallValue(value, epsilon = 0.0001) {
    if (typeof value !== "number") return value;
    return Math.abs(value) <= epsilon ? 0 : value;
}

/* =========================
   상태 메시지 처리
========================= */
function handleState(msg) {

    // battery
    if (msg.type === "battery") {
        document.getElementById("batteryText").textContent =
            (msg.data.percentage).toFixed(1) + "%";
    }

    // odometry
    if (msg.type === "odom") {
        const linear = clampSmallValue(msg.data.linear_vel.x);
        const angular = clampSmallValue(msg.data.angular_vel.z);
        
        document.getElementById("posText").textContent =
            `${msg.data.position.x.toFixed(2)}, ${msg.data.position.y.toFixed(2)}`;
        
        document.getElementById("velText").textContent =
            linear.toFixed(2);

        document.getElementById("angVelText").textContent =
            angular.toFixed(2);
    }

    // cmd_vel
    if (msg.type === "cmd_vel") {
        pass
    }

    // lidar sensor
    if (msg.type === "scan") {
        drawLidar(msg.data.ranges);
        console.log('msg.data.ranges : ',msg.data.ranges);
    }
}

/* =========================
   LIDAR VISUALIZATION
========================= */
function drawLidar(scan) {
    const canvas = document.getElementById("lidarCanvas");
    const ctx = canvas.getContext("2d");

    const W = canvas.width;
    const H = canvas.height;
    const cx = W / 2;
    const cy = H / 2;

    const maxRange = 5.0;   // meters (표시 최대 거리)

    ctx.clearRect(0, 0, W, H);

    /* ========= 방향 기준선 ========= */
    ctx.strokeStyle = "#cccccc";
    ctx.lineWidth = 1;
    ctx.font = "12px Arial";
    ctx.fillStyle = "#444";

    // Front (위)
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx, 0);
    ctx.stroke();
    ctx.fillText("Front", cx - 16, 12);

    // Back (아래)
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx, H);
    ctx.stroke();
    ctx.fillText("Back", cx - 16, H - 6);

    // Right (오른쪽)
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(W, cy);
    ctx.stroke();
    ctx.fillText("Right", W - 40, cy - 6);

    // Left (왼쪽)
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(0, cy);
    ctx.stroke();
    ctx.fillText("Left", 6, cy - 6);

    /* ========= 로봇 중심 ========= */
    ctx.fillStyle = "#000";
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.fill();

    if (!Array.isArray(scan) || scan.length === 0) return;

    /* ========= 라이다 데이터 ========= */
    const step = (2 * Math.PI) / scan.length;

    ctx.strokeStyle = "rgba(0,150,0,0.8)";
    ctx.lineWidth = 1;

    scan.forEach((dist, i) => {
        if (!isFinite(dist)) return;

        const angle = i * step - Math.PI / 2;
        // ↑ 0번 인덱스를 “정면(위)”로 맞춤

        const r = Math.min(dist / maxRange, 1.0) * (W / 2);

        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);

        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(x, y);
        ctx.stroke();
    });
}

/* =========================
   로봇 탭
========================= */
document.querySelectorAll(".robot-tab").forEach(tab => {
    tab.addEventListener("click", () => {

        // ✅ 모든 탭에서 active 제거
        document.querySelectorAll(".robot-tab")
            .forEach(t => t.classList.remove("active"));

        // ✅ 현재 클릭한 탭만 active
        tab.classList.add("active");

        // ✅ 로봇 이름 변경
        currentRobot = tab.dataset.robot;
        document.getElementById("currentRobotName").textContent = currentRobot;

        // ✅ WebSocket 재연결
        openCameraWS();
        openStateWS();
    });
});