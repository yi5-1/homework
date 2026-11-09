# 教學重點：跟 Week1/DAY6/web_basics 一樣的三層架構，
# 差別是這裡的「資料庫」換成即時去日文歌詞網站爬資料，並多接了一個翻譯 API。
#
#   手機/電腦瀏覽器 (HTML+JS)  <--HTTP-->  aiohttp (Python)  <--HTTP-->  J-Lyric.net / DeepL API
#         前端                                後端                           外部服務
#
# 資料的流動：
#   1. 使用者輸入歌名，按「搜尋」→ 前端打 GET /api/search
#   2. 後端去 J-Lyric.net 搜尋、把結果列表回傳給前端
#   3. 使用者點一首歌 → 前端打 GET /api/lyrics，後端爬該頁歌詞回傳
#   4. 使用者按「翻譯」→ 前端打 POST /api/translate，後端呼叫 DeepL 逐行翻譯
#   5. 使用者按「匯出」→ 前端打 POST /api/export，後端組成 .txt 讓瀏覽器下載

import os
import re
from pathlib import Path
from urllib.parse import quote, urljoin

from aiohttp import ClientSession, ClientTimeout, FormData, web
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).parent

搜尋網址 = "https://j-lyric.net/search.php"
標頭 = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}
逾時 = ClientTimeout(total=10)

DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY", "")
# 免費版 DeepL 金鑰結尾是 ":fx"，要打不同的 API 網址
DEEPL_網址 = (
    "https://api-free.deepl.com/v2/translate"
    if DEEPL_API_KEY.endswith(":fx")
    else "https://api.deepl.com/v2/translate"
)


# ====== 歌詞來源：J-Lyric.net ======
async def 搜尋歌曲(session, 歌名, 歌手=""):
    """回傳 [{"title", "artist", "url"}, ...]"""
    參數 = {"ex": "on", "kt": 歌名, "ct": 2, "ka": 歌手, "ca": 2, "kl": "", "cl": 2}
    async with session.get(搜尋網址, params=參數, headers=標頭, timeout=逾時) as 回應:
        回應.raise_for_status()
        內容 = await 回應.read()
    湯 = BeautifulSoup(內容, "html.parser")

    結果 = []
    for 區塊 in 湯.select("div.bdy"):
        連結標籤 = 區塊.select_one("p.mid a")
        歌手標籤 = 區塊.select_one("p.sml a")
        if not 連結標籤:
            continue
        結果.append({
            "title": 連結標籤.get_text(strip=True),
            "artist": 歌手標籤.get_text(strip=True) if 歌手標籤 else "未知歌手",
            "url": urljoin(搜尋網址, 連結標籤["href"]),
        })
    return 結果


async def 抓取歌詞(session, 網址):
    """回傳 (標題, 歌手, 歌詞文字)"""
    async with session.get(網址, headers=標頭, timeout=逾時) as 回應:
        回應.raise_for_status()
        內容 = await 回應.read()
    湯 = BeautifulSoup(內容, "html.parser")

    歌詞區 = 湯.select_one("p#Lyric")
    if 歌詞區 is None:
        raise ValueError("找不到歌詞內容，網站結構可能已變更")

    for 換行 in 歌詞區.find_all("br"):
        換行.replace_with("\n")
    歌詞文字 = 歌詞區.get_text().strip("\n")

    標題文字 = 湯.title.get_text(strip=True) if 湯.title else ""
    標題, _, 歌手 = 標題文字.partition("／")
    歌手 = 歌手.replace("歌詞", "").strip()
    return 標題.strip() or "未知歌名", 歌手 or "未知歌手", 歌詞文字


# ====== 翻譯：DeepL ======
async def 翻譯成中文(session, 原文行):
    """逐行翻譯，回傳跟原文行數一樣長的翻譯清單（空行維持空字串）"""
    if not DEEPL_API_KEY:
        raise ValueError("伺服器尚未設定 DEEPL_API_KEY")

    非空行 = [(索引, 行) for 索引, 行 in enumerate(原文行) if 行.strip()]
    輸出 = [""] * len(原文行)
    if not 非空行:
        return 輸出

    批次大小 = 50  # DeepL 一次請求最多接受 50 個 text 欄位
    for 起點 in range(0, len(非空行), 批次大小):
        批次 = 非空行[起點:起點 + 批次大小]

        表單 = FormData()
        表單.add_field("source_lang", "JA")
        表單.add_field("target_lang", "ZH-HANT")
        for _, 行 in 批次:
            表單.add_field("text", 行)

        認證標頭 = {"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"}
        async with session.post(DEEPL_網址, data=表單, headers=認證標頭, timeout=逾時) as 回應:
            if 回應.status != 200:
                錯誤內容 = await 回應.text()
                raise ValueError(f"DeepL 翻譯失敗（{回應.status}）：{錯誤內容[:200]}")
            結果 = await 回應.json()

        for (索引, _), 翻譯項 in zip(批次, 結果["translations"]):
            輸出[索引] = 翻譯項["text"]

    return 輸出


# ====== 後端層（HTTP routes）======
async def 首頁(request):
    return web.FileResponse(BASE / "static" / "index.html")


async def api_搜尋(request):
    歌名 = request.query.get("song", "").strip()
    歌手 = request.query.get("artist", "").strip()
    if not 歌名:
        return web.json_response({"error": "請輸入歌名"}, status=400)

    async with ClientSession() as session:
        try:
            結果 = await 搜尋歌曲(session, 歌名, 歌手)
        except Exception as 錯誤:
            return web.json_response({"error": f"搜尋失敗：{錯誤}"}, status=502)
    return web.json_response(結果)


async def api_歌詞(request):
    網址 = request.query.get("url", "")
    if not 網址.startswith("https://j-lyric.net/"):
        return web.json_response({"error": "不合法的網址"}, status=400)

    async with ClientSession() as session:
        try:
            標題, 歌手, 歌詞 = await 抓取歌詞(session, 網址)
        except Exception as 錯誤:
            return web.json_response({"error": f"載入歌詞失敗：{錯誤}"}, status=502)
    return web.json_response({"title": 標題, "artist": 歌手, "lyrics": 歌詞})


async def api_翻譯(request):
    data = await request.json()
    歌詞 = str(data.get("lyrics", ""))
    if not 歌詞.strip():
        return web.json_response({"error": "沒有歌詞可翻譯"}, status=400)

    async with ClientSession() as session:
        try:
            翻譯行 = await 翻譯成中文(session, 歌詞.split("\n"))
        except Exception as 錯誤:
            return web.json_response({"error": str(錯誤)}, status=502)
    return web.json_response({"translation": "\n".join(翻譯行)})


async def api_匯出(request):
    data = await request.json()
    標題 = str(data.get("title", "")).strip() or "歌詞"
    歌手 = str(data.get("artist", "")).strip()
    原文行 = str(data.get("lyrics", "")).split("\n")
    翻譯行 = str(data.get("translation", "")).split("\n")

    # 格式：標題 / 原文行 / 翻譯行 / 空行，逐句配對，跳過原文的空行
    段落 = [標題]
    for 索引, 原文句 in enumerate(原文行):
        if not 原文句.strip():
            continue
        段落.append(原文句)
        if 索引 < len(翻譯行) and 翻譯行[索引].strip():
            段落.append(翻譯行[索引])
        段落.append("")

    while 段落 and 段落[-1] == "":
        段落.pop()

    內容 = "\n".join(段落).encode("utf-8")
    檔名 = re.sub(r'[\\/:*?"<>|]', "_", f"{標題}_{歌手}.txt".strip("_"))

    return web.Response(
        body=內容,
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(檔名)}",
        },
    )


# ====== 啟動 ======
def main():
    app = web.Application()
    app.router.add_get("/", 首頁)
    app.router.add_get("/api/search", api_搜尋)
    app.router.add_get("/api/lyrics", api_歌詞)
    app.router.add_post("/api/translate", api_翻譯)
    app.router.add_post("/api/export", api_匯出)

    # Render 會用環境變數 PORT 指定要監聽的埠號；本機測試就用 .env 的 SERVER_PORT
    port = int(os.environ.get("PORT") or os.environ.get("SERVER_PORT") or 8000)
    print(f"Server 開啟於 http://0.0.0.0:{port}/  (Ctrl+C 停止)")
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
