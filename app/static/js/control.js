// =========================================================
// app/static/js/control.js
// 역할:
// - 이동 버튼 클릭 → 이동 명령 전송
// - UI / WebSocket / 상태 관리는 관여하지 않음
// =========================================================

function getCurrentRobot() {
    return window.AppState?.selectedRobot || "";
}

/* =========================
   이동 명령 전송
========================= */
async function sendGoal(target) {
    const robot = getCurrentRobot();
    if (!robot) {
        alert("로봇이 선택되지 않았습니다.");
        return;
    }

    try {
        const res = await fetch(
            `/control/api/${encodeURIComponent(robot)}/goto?target=${encodeURIComponent(target)}`,
            { method: "POST" }
        );

        if (!res.ok) {
            alert("이동 실패: " + await res.text());
        } else {
            console.log(`[CONTROL] ${robot} → ${target}`);
        }
    } catch (err) {
        console.error("[CONTROL] fetch error", err);
    }
}

/* =========================
   버튼 이벤트 바인딩
========================= */
function setupControlButtons() {
    const bind = (id, target) => {
        const el = document.getElementById(id);
        if (!el) return;          // 버튼이 없으면 아무것도 하지 않음
        el.onclick = () => sendGoal(target);
    };

    bind("btn-wait", "wait");

    bind("btn-entrance-1", "entrance_1");
    bind("btn-entrance-2", "entrance_2");
    bind("btn-entrance-3", "entrance_3");

    bind("btn-exit-1", "exit_1");
    bind("btn-exit-2", "exit_2");
    bind("btn-exit-3", "exit_3");
}

/* =========================
   Init
========================= */
window.addEventListener("DOMContentLoaded", () => {
    setupControlButtons();
});
