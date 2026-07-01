# 教學重點：把前面學的全部組起來做一個小作品
# 用到：Tk()、Label、Entry、Button、grid、messagebox

import tkinter as tk
from tkinter import messagebox

window = tk.Tk()
window.title("BMI 計算機")
window.geometry("300x200")

# 第 0 列：身高
tk.Label(window, text="身高 (公分)：").grid(row=0, column=0, padx=10, pady=10)
身高輸入 = tk.Entry(window)
身高輸入.grid(row=0, column=1)

# 第 1 列：體重
tk.Label(window, text="體重 (公斤)：").grid(row=1, column=0, padx=10, pady=10)
體重輸入 = tk.Entry(window)
體重輸入.grid(row=1, column=1)

# 第 3 列：結果
結果 = tk.Label(window, text="BMI 會顯示在這裡", fg="blue")
結果.grid(row=3, column=0, columnspan=2, pady=10)

def 計算BMI():
    try:
        h = float(身高輸入.get()) / 100   # 公分轉公尺
        w = float(體重輸入.get())
        bmi = w / (h * h)
        結果.config(text=f"你的 BMI = {bmi:.2f}")
    except ValueError:
        # 萬一使用者沒輸入或輸入亂打，跳警告視窗
        messagebox.showerror("錯誤", "請輸入正確的數字！")

tk.Button(window, text="計算", command=計算BMI).grid(row=2, column=0, columnspan=2, pady=5)

window.mainloop()
