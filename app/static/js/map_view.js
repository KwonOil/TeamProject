// app/static/js/map_view.js

/**
 * =========================================================
 * 1단계 목표:
 * - SLAM 맵 이미지를 canvas에 그린다.
 * - 로봇 위치(x,y)를 받아 map 위에 점을 찍는다.
 *
 * 서버에서 /map/info 로 내려주는 값:
 *  - image_url: "/static/maps/airport_map.png"
 *  - resolution: 0.05
 *  - origin: [-10.0, -10.0, 0.0]
 *
 * 좌표 변환 공식 (ROS map 좌표 -> Canvas 픽셀):
 *  px = (x - origin_x) / resolution
 *  py = map_height_px - (y - origin_y) / resolution
 *
 * 이유:
 * - ROS 좌표계는 y가 위로 증가
 * - Canvas는 y가 아래로 증가
 * =========================================================
 */

window.MapView = (() => {
    let canvas = null;
    let ctx = null;

    // map meta
    let mapInfo = null;
    let mapImage = null;

    // 로봇 위치(최신)
    let robotPose = { x: null, y: null };

    function setStatus(text) {
        const el = document.getElementById("mapStatusText");
        if (el) el.textContent = text;
    }

    async function loadMapInfo() {
        const res = await fetch("/map/info");
        if (!res.ok) {
            throw new Error(await res.text());
        }
        return await res.json();
    }

    function loadImage(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = (e) => reject(e);
            img.src = url;
        });
    }

    function initCanvasSizeToImage(img) {
        // canvas의 실제 픽셀 크기를 이미지에 맞춤
        // (CSS max-width:100%는 화면 표시만 줄이고 내부 좌표계는 유지)
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
    }

    function worldToPixel(x, y) {
        // mapInfo.origin: [origin_x, origin_y, origin_yaw]
        const originX = mapInfo.origin[0];
        const originY = mapInfo.origin[1];
        const res = mapInfo.resolution;

        const px = (x - originX) / res;
        const py = canvas.height - (y - originY) / res;
        return { px, py };
    }

    function draw() {
        if (!ctx || !mapImage) return;

        // 1) 맵 배경 그리기
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(mapImage, 0, 0);

        // 2) 로봇 점 그리기 (위치가 있을 때만)
        if (robotPose.x == null || robotPose.y == null) return;

        const { px, py } = worldToPixel(robotPose.x, robotPose.y);

        // 캔버스 밖이면 그리지 않음(좌표 불일치 디버깅에 도움)
        if (px < 0 || py < 0 || px > canvas.width || py > canvas.height) {
            // 좌표가 안 맞을 때 바로 알아차리라고 상태 표시
            setStatus(`pose out of map (x=${robotPose.x.toFixed(2)}, y=${robotPose.y.toFixed(2)})`);
            return;
        }

        // 로봇 점 (빨간 원)
        ctx.beginPath();
        ctx.arc(px, py, 6, 0, Math.PI * 2);
        ctx.fillStyle = "red";
        ctx.fill();

        // 간단한 테두리
        ctx.lineWidth = 2;
        ctx.strokeStyle = "white";
        ctx.stroke();

        setStatus("ok");
    }

    async function init() {
        canvas = document.getElementById("mapCanvas");
        if (!canvas) return; // 해당 페이지에 맵 캔버스가 없으면 아무것도 하지 않음
        ctx = canvas.getContext("2d");

        try {
            setStatus("loading map info...");
            mapInfo = await loadMapInfo();

            setStatus("loading map image...");
            mapImage = await loadImage(mapInfo.image_url);

            initCanvasSizeToImage(mapImage);
            setStatus("ready");

            // 최초 1회 그리기
            draw();
        } catch (err) {
            console.error("[MAP] init error:", err);
            setStatus("failed to load map");
        }
    }

    function updatePose(x, y) {
        // 외부(dashboard.js)에서 odom을 받으면 이 함수만 호출해주면 된다.
        robotPose.x = x;
        robotPose.y = y;
        draw();
    }

    return {
        init,
        updatePose,
    };
})();

window.addEventListener("DOMContentLoaded", () => {
    // 페이지 로드시 맵을 로드
    window.MapView.init();
});
