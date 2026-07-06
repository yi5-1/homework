# 專題 E 起手式：即時視覺監控站（能跑的最小骨架）
#
# 一台電腦接鏡頭，把每一格影像壓成 JPEG → base64，透過 WebSocket 廣播給所有瀏覽器。
# 任何裝置打開 http://<本機IP>:8765/ 就能同時看到即時畫面。
#
# 架構跟 web_shooter 一樣：server 定時廣播 → 多個 WebSocket client 接收。
# 只是廣播的內容從「遊戲狀態」換成「一張影像」。
#
# 你要接手加的：
#   - 前端按鈕切濾鏡（灰階/Canny/模糊，server 端套 DAY7 學的處理再送）
#   - 顯示線上人數、動作偵測存快照進 DB、FPS 顯示

import asyncio
import base64
from pathlib import Path

import cv2
from aiohttp import web, WSMsgType

BASE = Path(__file__).parent
連線中 = set()          # 所有 WebSocket client
影像寬, 影像高 = 320, 240  # 先縮小才不會卡（影像比遊戲狀態大很多）
JPEG_品質 = 60
每秒張數 = 12


async def 首頁(request):
    return web.FileResponse(BASE / "index.html")


async def websocket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    連線中.add(ws)
    print(f"新觀看者，目前 {len(連線中)} 人")
    try:
        async for msg in ws:
            # 前端未來可送 {"filter": "canny"} 來切濾鏡（TODO）
            if msg.type == WSMsgType.ERROR:
                break
    finally:
        連線中.discard(ws)
        print(f"離開，剩 {len(連線中)} 人")
    return ws


async def 擷取並廣播(app):
    """背景工作：一直讀鏡頭，把影像廣播給所有 client。"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("錯誤：無法開啟鏡頭。")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 影像寬)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 影像高)

    try:
        while True:
            ret, frame = cap.read()
            if ret and 連線中:
                frame = cv2.resize(frame, (影像寬, 影像高))
                # TODO(加分)：依前端選的濾鏡處理，例如 cv2.Canny(灰階, 100, 200)
                ok, buf = cv2.imencode(".jpg", frame,
                                       [cv2.IMWRITE_JPEG_QUALITY, JPEG_品質])
                if ok:
                    b64 = base64.b64encode(buf).decode("ascii")
                    payload = "data:image/jpeg;base64," + b64
                    # 廣播給所有人；慢的 client 不阻塞別人
                    await asyncio.gather(
                        *(ws.send_str(payload) for ws in list(連線中)),
                        return_exceptions=True,
                    )
            await asyncio.sleep(1 / 每秒張數)
    finally:
        cap.release()


async def on_startup(app):
    app["擷取任務"] = asyncio.create_task(擷取並廣播(app))


async def on_cleanup(app):
    app["擷取任務"].cancel()


def build_app():
    app = web.Application()
    app.router.add_get("/", 首頁)
    app.router.add_get("/ws", websocket)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


if __name__ == "__main__":
    print("監控站開啟於 http://0.0.0.0:8765/  （同網段裝置用瀏覽器連本機 IP）")
    web.run_app(build_app(), host="0.0.0.0", port=8765)
