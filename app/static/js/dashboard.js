// =========================================================
// app/static/js/dashboard.js
//
// 역할:
// 1. 선택된 로봇(AppState) 기준으로 WebSocket 연결
// 2. 상태 메시지(type별) 처리
// 3. Dashboard UI 업데이트
// 4. 로봇 선택 탭 처리
// 5. 로봇 조작 패널 토글 (UI 전용)
//
// ❗ 캐시 사용 안 함
// ❗ 상태 처리 진입점은 handleState 하나뿐
// =========================================================


/* =========================================================
   Global Robot State
========================================================= */
function getCurrentRobot() {
    return window.AppState?.selectedRobot || "";
}

function setCurrentRobot(robot) {
    if (!window.AppState) window.AppState = {};
    window.AppState.selectedRobot = robot;
}


/* =========================================================
   WebSocket Handles
========================================================= */
let camWs = null;
let stateWs = null;


/* =========================================================
   Camera WebSocket (영상 전용)
========================================================= */
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

        const img = document.getElementById("cam");
        if (!img) return;

        const blob = new Blob([e.data], { type: "image/jpeg" });
        img.src = URL.createObjectURL(blob);
    };
}


/* =========================================================
   State WebSocket (배터리 / odom / scan)
========================================================= */
function openStateWS() {
    const robot = getCurrentRobot();
    if (!robot) return;

    if (stateWs) stateWs.close();

    const url = `ws://${location.host}/state/view/robot/${encodeURIComponent(robot)}`;
    console.log("[STATE][WS]", url);

    stateWs = new WebSocket(url);

    stateWs.onmessage = e => {
        try {
            const msg = JSON.parse(e.data);
            handleState(msg);
        } catch (err) {
            console.error("[STATE][PARSE ERROR]", err, e.data);
        }
    };
}


/* =========================================================
   State Message Dispatcher (핵심)
========================================================= */
function handleState(msg) {
    console.log("[STATE]", msg);
    if (!msg || !msg.type) return;

    switch (msg.type) {
        case "battery":
            handleBattery(msg.data);
            break;

        case "odom":
            handleOdom(msg.data);
            break;

        case "scan":
            handleScan(msg.data);
            break;

        case "cmd_vel":
            handleCmdVel(msg.data);
            break;

        default:
            // 필요 없는 타입은 무시
            break;
    }
}


/* =========================================================
   Battery Handler
========================================================= */
function handleBattery(data) {
    if (!data?.percentage) return;

    const el = document.getElementById("batteryText");
    if (!el) return;

    el.textContent = `${Number(data.percentage).toFixed(1)}%`;
}


/* =========================================================
   Odometry Handler
   - 위치
   - 실제 속도 (twist 기반)
   - 맵 표시
========================================================= */
function handleOdom(data) {
    if (!data) return;

    const pos = data.position;
    // const twist = data.twist;

    // 위치
    if (pos) {
        const posEl = document.getElementById("posText");
        if (posEl) {
            posEl.textContent =
                `${pos.x.toFixed(2)}, ${pos.y.toFixed(2)}`;
        }

        // 맵 표시 (1회만)
        if (window.MapView && typeof window.MapView.updatePose === "function") {
            window.MapView.updatePose(pos.x, pos.y);
        }
    }

    // 실제 이동 속도
    // if (twist) {
    //     const velEl = document.getElementById("velText");
    //     const angEl = document.getElementById("angVelText");

    //     if (velEl) velEl.textContent = twist.linear.x.toFixed(2);
    //     if (angEl) angEl.textContent = twist.angular.z.toFixed(2);
    // }
}

/* =========================================================
   CmdVel Handler
========================================================= */
function handleCmdVel(data) {
    const velEl = document.getElementById("velText");
    const angEl = document.getElementById("angVelText");

    if (velEl) velEl.textContent = data.linear.x.toFixed(2);
    if (angEl) angEl.textContent = data.angular.z.toFixed(2);
}


/* =========================================================
   LIDAR Handler
========================================================= */
function handleScan(data) {
    if (!data?.ranges) return;

    drawLidar(data.ranges);
}


/* =========================================================
   LIDAR Visualization
========================================================= */
function drawLidar(scan) {
    const canvas = document.getElementById("lidarCanvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    const W = canvas.width;
    const H = canvas.height;
    const cx = W / 2;
    const cy = H / 2;

    const maxRange = 5.0;

    ctx.clearRect(0, 0, W, H);

    // 기준선
    ctx.strokeStyle = "#ccc";
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.moveTo(cx, cy); ctx.lineTo(cx, 0); ctx.stroke();      // Front
    ctx.beginPath();
    ctx.moveTo(cx, cy); ctx.lineTo(cx, H); ctx.stroke();      // Back
    ctx.beginPath();
    ctx.moveTo(cx, cy); ctx.lineTo(W, cy); ctx.stroke();      // Right
    ctx.beginPath();
    ctx.moveTo(cx, cy); ctx.lineTo(0, cy); ctx.stroke();      // Left

    // 로봇 중심
    ctx.fillStyle = "#000";
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.fill();

    if (!Array.isArray(scan) || scan.length === 0) return;

    const step = (2 * Math.PI) / scan.length;

    ctx.strokeStyle = "rgba(0,150,0,0.8)";
    ctx.lineWidth = 1;

    scan.forEach((dist, i) => {
        if (!isFinite(dist)) return;

        const angle = i * step - Math.PI / 2;
        const r = Math.min(dist / maxRange, 1.0) * (W / 2);

        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);

        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(x, y);
        ctx.stroke();
    });
}


/* =========================================================
   Control Panel Toggle (UI 전용)
========================================================= */
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


/* =========================================================
   Robot Tabs
========================================================= */
function setupRobotTabs() {
    document.querySelectorAll(".robot-tab").forEach(tab => {
        tab.addEventListener("click", async () => {
            const robot = tab.dataset.robot;

            document.querySelectorAll(".robot-tab")
                .forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            setCurrentRobot(robot);

            document.getElementById("currentRobotName").textContent = robot;
            document.getElementById("controlRobotName").textContent = robot;

            await fetch("/api/select_robot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ robot })
            });

            openCameraWS();
            openStateWS();
        });
    });
}


/* =========================================================
   Init
========================================================= */
window.addEventListener("DOMContentLoaded", () => {
    if (getCurrentRobot()) {
        openCameraWS();
        openStateWS();
    }
    setupControlToggle();
    setupRobotTabs();
});
