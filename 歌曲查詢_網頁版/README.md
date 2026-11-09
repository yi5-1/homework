# 歌曲查詢（網頁版）

[歌曲查詢.py](歌曲查詢.py)（tkinter 桌機版）的網頁版本，讓手機（含 iPhone）也能透過瀏覽器使用，並且串接 DeepL API 自動把日文歌詞翻譯成繁體中文。

- 歌詞來源：[J-Lyric.net](https://j-lyric.net/)
- 翻譯：[DeepL API](https://www.deepl.com/pro-api)（免費額度每月 50 萬字元）

## 本機執行

```bash
pip install -r requirements.txt
cp .env.example .env   # 填入你的 DEEPL_API_KEY
python server.py       # http://127.0.0.1:8000/
```

手機要連本機測試，手機和電腦要在同一個 Wi-Fi，網址改成電腦的區網 IP，例如 `http://192.168.1.5:8000/`（可用 `ipconfig` 查電腦 IP）。

## 部署到 Render（讓任何網路都能連）

1. 到 [DeepL API](https://www.deepl.com/pro-api) 申請免費帳號，拿到 API Key。
2. 把這個 repo push 到 GitHub。
3. 到 [Render](https://render.com) 註冊帳號，選 **New + → Blueprint**，選這個 repo（repo 根目錄已經有 `render.yaml`，Render 會自動抓到設定）。
4. 部署時系統會要求輸入 `DEEPL_API_KEY`，貼上步驟 1 拿到的金鑰。
5. 等建置完成，Render 會給一個公開網址（例如 `https://song-lyrics-translator.onrender.com`），手機直接開這個網址就能用。

若不想用 Blueprint，也可以手動在 Render 開 **New Web Service**：
- Root Directory：`歌曲查詢_網頁版`
- Build Command：`pip install -r requirements.txt`
- Start Command：`python server.py`
- 環境變數：`DEEPL_API_KEY`

> 免費方案的服務閒置一段時間會休眠，重新被打開時第一次連線會慢個幾十秒，屬正常現象。

## API

| Method | 路徑 | 說明 |
|---|---|---|
| GET | `/api/search?song=歌名&artist=歌手` | 搜尋歌曲，回傳 `[{title, artist, url}, ...]` |
| GET | `/api/lyrics?url=歌詞頁網址` | 抓取歌詞，回傳 `{title, artist, lyrics}` |
| POST | `/api/translate` | body `{lyrics}` → 回傳 `{translation}`（逐行對齊） |
| POST | `/api/export` | body `{title, artist, lyrics, translation}` → 回傳可下載的 `.txt` |
