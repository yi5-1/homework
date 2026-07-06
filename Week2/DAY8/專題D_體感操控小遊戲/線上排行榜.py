# 對接「專題 B 多人網頁遊戲排行榜」服務的小工具。
#
# B 專案（Week2/DAY8/專題B_多人網頁遊戲排行榜）預設跑在 http://localhost:8770，提供：
#   POST /api/score        body: {"name": str, "kills": int}  → 存一筆成績
#   GET  /api/leaderboard                                     → 回擊殺數前 10 名 JSON
#
# 這支只用標準函式庫（urllib），不額外加 requests 依賴，全部包 try/except + 短 timeout：
# B 的服務沒開時，遊戲仍然要能正常跑、自動退回本機 ranking.json 排行榜
# （呼叫端看到 None 就退回，見 專題_閃避隕石.py 的 ST_結束 那段）。

import json
import urllib.error
import urllib.request

服務位址 = "http://localhost:8770"
逾時秒數 = 1.5


def 送分數(name, score):
    """
    把一局的成績丟給 B 的排行榜服務。
    B 的欄位叫 kills（沿用它射擊遊戲的命名），這裡直接拿本遊戲的存活分數當值即可——
    B 那邊只是拿數字排序、顯示，不在意語意上是「擊殺數」還是「分數」。
    回傳 True/False 代表有沒有送成功；送失敗不影響遊戲，本機排行榜仍會照存。
    """
    try:
        body = json.dumps({"name": name, "kills": int(score)}).encode("utf-8")
        req = urllib.request.Request(
            f"{服務位址}/api/score", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=逾時秒數) as resp:
            return resp.status == 200
    except Exception:
        return False


def 取得線上排行榜():
    """
    取得 B 服務的前十名，格式為 [{"name": str, "kills": int}, ...]。
    服務沒開 / 逾時 / 回傳格式錯誤都回傳 None，呼叫端應該在拿到 None 時
    退回本機排行榜（今日排行()）。
    """
    try:
        with urllib.request.urlopen(f"{服務位址}/api/leaderboard", timeout=逾時秒數) as resp:
            資料 = json.loads(resp.read().decode("utf-8"))
        if not isinstance(資料, list):
            return None
        return 資料
    except Exception:
        return None
