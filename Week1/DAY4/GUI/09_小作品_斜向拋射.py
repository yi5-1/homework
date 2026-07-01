# 教學重點：把 DAY2 的「斜向拋射」函式套上 GUI
# 用到：Entry 輸入、Button 觸發、Label 顯示結果、grid 排版、messagebox 防呆

import math
import tkinter as tk
from tkinter import messagebox

def 射射射(v0, angle):
    g = 9.8
    theta = math.radians(angle)
    T = (2 * v0 * math.sin(theta)) / g
    H = ((v0 * math.sin(theta)) ** 2) / (2 * g)
    R = (v0 ** 2 * math.sin(2 * theta)) / g
    return T, H, R

window = tk.Tk()
window.title("斜向拋射計算機")
window.geometry("320x220")

tk.Label(window, text="初速 v0 (m/s)：").grid(row=0, column=0, padx=10, pady=8, sticky="e")
v0_輸入 = tk.Entry(window)
v0_輸入.grid(row=0, column=1)

tk.Label(window, text="角度 (°)：").grid(row=1, column=0, padx=10, pady=8, sticky="e")
角度_輸入 = tk.Entry(window)
角度_輸入.grid(row=1, column=1)

結果 = tk.Label(window, text="結果會顯示在這裡", fg="blue", justify="left")
結果.grid(row=3, column=0, columnspan=2, pady=10)

def 計算():
    try:
        v0 = float(v0_輸入.get())
        angle = float(角度_輸入.get())
        T, H, R = 射射射(v0, angle)
        結果.config(text=f"飛行時間 T = {T:.2f} 秒\n最大高度 H = {H:.2f} 公尺\n水平射程 R = {R:.2f} 公尺")
    except ValueError:
        messagebox.showerror("錯誤", "請輸入正確的數字！")

tk.Button(window, text="計算", command=計算).grid(row=2, column=0, columnspan=2, pady=5)

window.mainloop()
