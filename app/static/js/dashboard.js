// =========================================================
// app/static/js/dashboard.js
// 역할:
// - 전역 로봇 상태(AppState) 관리
// - Camera / State WebSocket 연결
// - 로봇 상태 UI 업데이트
// - 로봇 선택 탭 처리
// - 로봇 조작 패널 토글(UI)
// =========================================================

/* =========================
   Global State Access
========================= */
function getCurrentRobot() {
    return window.AppState?.selectedRobot || "";
}

function setCurrentRobot(robot) {
    window.AppState.selectedRobot = robot;
}

/* =========================
   WebSocket Handles
========================= */
let camWs = null;
let stateWs = null;

/* =========================
   Camera WebSocket
========================= */
function openCameraWS() {
    const robot = getCurrentRobot();
    if (!robot) return;

    if (camWs) camWs.close();

    const url = `ws://${location.host}/camera/view/robot/${encodeURIComponent(robot)}`;
    console.log("[CAMERA][WS]", url);

    camWs = new WebSocket(url);
    camWs.binaryType = "arraybuffer";

    camWs.onmessage = e => {
        if (!(e.data instanceof ArrayBuffer)) return;

        const imgEl = document.getElementById("cam");
        if (!imgEl) return;

        const blob = new Blob([e.data], { type: "image/jpeg" });
        imgEl.src = URL.createObjectURL(blob);
    };
}

/* =========================
   State WebSocket
========================= */
function openStateWS() {
    const robot = getCurrentRobot();
    if (!robot) return;

    if (stateWs) stateWs.close();

    const url = `ws://${location.host}/state/view/robot/${encodeURIComponent(robot)}`;
    console.log("[STATE][WS]", url);

    stateWs = new WebSocket(url);

    stateWs.onmessage = e => {
        try {
            handleState(JSON.parse(e.data));
        } catch (err) {
            console.error("[STATE][PARSE ERROR]", err);
        }
    };
}

/* =========================
   State Handler
========================= */
function handleState(msg) {
    console.log("[STATE]", msg);

    // 배터리
    if (msg.type === "battery") {
        document.getElementById("batteryText").textContent =
            `${Number(msg.data.percentage).toFixed(1)}%`;
    }

    // 위치 + 속도 (odom)
    if (msg.type === "odom") {
        const pos = msg.data.position;
        const twist = msg.data.twist;

        if (pos) {
            document.getElementById("posText").textContent =
                `${pos.x.toFixed(2)}, ${pos.y.toFixed(2)}`;

            // 맵 표시
            if (window.MapView) {
                window.MapView.updatePose(pos.x, pos.y);
            }
        }

        if (twist) {
            // ✅ 실제 이동 속도
            document.getElementById("velText").textContent =
                twist.linear.x.toFixed(2);

            document.getElementById("angVelText").textContent =
                twist.angular.z.toFixed(2);
        }
    }
}

/* =========================
   Control Panel Toggle (UI ONLY)
========================= */
function setupControlToggle() {
    const btn = document.getElementById("toggleControlBtn");
    const panel = document.getElementById("controlPanel");

    if (!btn || !panel) return;

    btn.addEventListener("click", () => {
        const opened = panel.style.display === "block";
        panel.style.display = opened ? "none" : "block";
        btn.textContent = opened ? "로봇 조작" : "조작 패널 닫기";
    });
}

/* =========================
   Robot Tabs
========================= */
function setupRobotTabs() {
    document.querySelectorAll(".robot-tab").forEach(tab => {
        tab.addEventListener("click", async () => {
            const robot = tab.dataset.robot;

            // UI
            document.querySelectorAll(".robot-tab")
                .forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            // State
            setCurrentRobot(robot);

            document.getElementById("currentRobotName").textContent = robot;
            document.getElementById("controlRobotName").textContent = robot;

            // Server session
            await fetch("/api/select_robot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ robot })
            });

            // Reconnect WS
            openCameraWS();
            openStateWS();
        });
    });
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
   Init
========================= */
window.addEventListener("DOMContentLoaded", () => {
    if (getCurrentRobot()) {
        openCameraWS();
        openStateWS();
    }
    setupControlToggle();
    setupRobotTabs();
});