# 專題 A 起手式：智慧視覺打卡系統（能跑的最小骨架）
#
# 現在會做的事：
#   1. 開鏡頭即時顯示
#   2. 按 SPACE 幫「目前姓名」打一次卡，寫進 SQLite
#   3. 按 c 跳出 matplotlib 出勤統計圖
#   4. 按 n 重新輸入姓名（在終端機打）、按 q 離開
#
# 你要接手加的（README 的必做 / 加分，程式裡用 TODO 標出來）：
#   - 影格差異自動打卡、tkinter GUI 包起來、遲到判斷、匯出 Excel …

import sqlite3
from datetime import datetime
from pathlib import Path

import cv2

BASE = Path(__file__).parent
DB_PATH = BASE / "attendance.db"


# ====== 資料庫層 ======
def 初始化資料庫():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS 打卡紀錄 (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               姓名 TEXT NOT NULL,
               時間 TEXT NOT NULL
           )"""
    )
    conn.commit()
    return conn


def 新增打卡(conn, 姓名):
    現在 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO 打卡紀錄 (姓名, 時間) VALUES (?, ?)", (姓名, 現在))
    conn.commit()
    print(f"[打卡] {姓名} @ {現在}")


def 統計每人次數(conn):
    cur = conn.execute(
        "SELECT 姓名, COUNT(*) FROM 打卡紀錄 GROUP BY 姓名 ORDER BY COUNT(*) DESC"
    )
    return cur.fetchall()  # [(姓名, 次數), ...]


# ====== 統計圖 ======
def 顯示統計圖(conn):
    資料 = 統計每人次數(conn)
    if not 資料:
        print("目前還沒有任何打卡紀錄。")
        return

    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]  # 中文不變方框
    plt.rcParams["axes.unicode_minus"] = False

    姓名清單 = [r[0] for r in 資料]
    次數清單 = [r[1] for r in 資料]

    plt.figure("出勤統計")
    plt.bar(姓名清單, 次數清單, color="#4C72B0")
    plt.title("每人打卡次數")
    plt.ylabel("次數")
    plt.tight_layout()
    plt.show()
    # TODO(加分)：改成出勤/缺席圓餅圖、遲到用不同顏色


# ====== 主程式 ======
def main():
    conn = 初始化資料庫()

    姓名 = input("請輸入你的姓名：").strip() or "訪客"

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("錯誤：無法開啟鏡頭。可先不接鏡頭，改用終端機測試資料庫函式。")
        return

    print("SPACE=打卡  c=看統計圖  n=改姓名  q=離開")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 畫面上疊資訊（cv2.putText 只吃英文，中文請用 matplotlib/GUI 呈現）
        cv2.putText(frame, f"Name: {姓名}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, "SPACE=punch  c=chart  n=name  q=quit", (10, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # TODO(加分)：這裡加「影格差異」偵測，畫面有人變化就自動打卡
        cv2.imshow("attendance", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord(" "):
            新增打卡(conn, 姓名)
        elif key == ord("c"):
            顯示統計圖(conn)
        elif key == ord("n"):
            姓名 = input("新姓名：").strip() or 姓名

    cap.release()
    cv2.destroyAllWindows()
    conn.close()


if __name__ == "__main__":
    main()
