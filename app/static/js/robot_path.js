// app/static/js/robot_path.js
const robotName = window.ROBOT_NAME;

// Chart.js 그래프 초기화
let ctx = document.getElementById("pathCanvas").getContext("2d");

let chart = new Chart(ctx, {
    type: "line",
    data: {
        datasets: [{
            label: "Robot Path",
            data: [],
            borderColor: "green",
            borderWidth: 2,
            pointRadius: 2,
            fill: false,
            tension: 0   // 직선
        }]
    },
    options: {
        responsive: false,
        maintainAspectRatio: false,
        scales: {
            x: {
                type: "linear",
                min: -40,
                max: 40
            },
            y: {
                type: "linear",
                min: -40,
                max: 40
            }
        }
    }
});
function loadPath() {
    const start = document.getElementById("startTime").value;
    const end   = document.getElementById("endTime").value;

    // datetime-local → 초 추가
    const startFix = start + ":00";
    const endFix   = end + ":00";

    fetch(`/path/api/robot/${robotName}/path?start=${startFix}&end=${endFix}`)
        .then(r => r.json())
        .then(data => {
            console.log("로드된 경로:", data.points);

            const points = data.points.map(p => ({ x: p.x, y: -p.y }));

            chart.data.datasets[0].data = points;
            chart.update();
        });
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("loadPath").addEventListener("click", loadPath);
});