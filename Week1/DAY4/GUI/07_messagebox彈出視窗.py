# 教學重點：用 messagebox 彈出小視窗（提示 / 警告 / 詢問）
# 重要觀念：要 from tkinter import messagebox 才能用

import tkinter as tk
from tkinter import messagebox

window = tk.Tk()
window.title("messagebox 練習")
window.geometry("400x300")

def 顯示資訊():
    # 藍色 i 圖示，純資訊
    messagebox.showinfo("提示", "這是一則訊息")

def 顯示警告():
    # 黃色三角形警告
    messagebox.showwarning("注意", "你按下了警告按鈕！")

def 顯示錯誤():
    # 紅色叉叉
    messagebox.showerror("錯誤", "發生錯誤了！")

def 問問題():
    # 詢問是否，會回傳 True / False
    答案 = messagebox.askyesno("確認", "你確定要繼續嗎？")
    print("使用者選擇：", 答案)

tk.Button(window, text="提示", command=顯示資訊).pack(pady=5)
tk.Button(window, text="警告", command=顯示警告).pack(pady=5)
tk.Button(window, text="錯誤", command=顯示錯誤).pack(pady=5)
tk.Button(window, text="詢問是非", command=問問題).pack(pady=5)

window.mainloop()
