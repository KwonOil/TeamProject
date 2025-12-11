// app/static/js/control.js

let currentRobot = window.INITIAL_ROBOT_NAME || "";

/**
 * API 호출 공통 함수
 * target: "wait", "entrance_1", "exit_2" 같은 문자열
 */
async function sendGoal(target) {
    if (!currentRobot) {
        alert("로봇이 선택되지 않았습니다.");
        return;
    }

    try {
        const res = await fetch(
            `/control/api/${encodeURIComponent(currentRobot)}/goto?target=${target}`,
            { method: "POST" }
        );

        if (!res.ok) {
            const text = await res.text();
            alert("이동 실패: " + text);
            return;
        }

        console.log(`✅ Goal sent: ${target}`);
    } catch (err) {
        console.error(err);
        alert("서버 통신 오류");
    }
}


/**
 * 좌측 탭 클릭 시 선택 상태 변경
 */
function setupRobotTabs() {
    document.querySelectorAll(".robot-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            // 모든 탭에서 active 제거
            document.querySelectorAll(".robot-tab")
                .forEach(t => t.classList.remove("active"));

            // 현재 탭만 active
            tab.classList.add("active");

            // 현재 로봇 이름 변경
            currentRobot = tab.dataset.robot;
            document.getElementById("currentRobotName").textContent = currentRobot;
        });
    });
}

/**
 * 버튼에 이벤트 연결
 */
function setupButtons() {
    document.getElementById("btn-wait")
        .addEventListener("click", () => sendMoveCommand("wait"));

    document.getElementById("btn-entrance-1")
        .addEventListener("click", () => sendMoveCommand("entrance_1"));
    document.getElementById("btn-entrance-2")
        .addEventListener("click", () => sendMoveCommand("entrance_2"));
    document.getElementById("btn-entrance-3")
        .addEventListener("click", () => sendMoveCommand("entrance_3"));

    document.getElementById("btn-exit-1")
        .addEventListener("click", () => sendMoveCommand("exit_1"));
    document.getElementById("btn-exit-2")
        .addEventListener("click", () => sendMoveCommand("exit_2"));
    document.getElementById("btn-exit-3")
        .addEventListener("click", () => sendMoveCommand("exit_3"));
}

window.addEventListener("DOMContentLoaded", () => {
    setupRobotTabs();
    setupButtons();
});
