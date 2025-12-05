function loadPath() {
    const start = document.getElementById("start").value;
    const end   = document.getElementById("end").value;

    // datetime-local → 초 추가
    const startFix = start + ":00";
    const endFix   = end + ":00";

    fetch(`/api/robot/${robotName}/path?start=${startFix}&end=${endFix}`)
        .then(r => r.json())
        .then(data => {
            console.log("로드된 경로:", data.points);

            const points = data.points.map(p => ({ x: p.x, y: -p.y }));

            chart.data.datasets[0].data = points;
            chart.update();
        });
}
