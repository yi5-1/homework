# 教學重點：Entry 單行輸入框，取得使用者打的字
# 重要觀念：用 .get() 拿到使用者輸入的內容

import tkinter as tk
from tkinter import messagebox
window = tk.Tk()
window.title("Entry 練習")
window.geometry("400x300")

labelA = tk.Label(window, text="請輸入A").pack()
# 建立輸入框
entryA = tk.Entry(window)
entryA.pack()
labelB = tk.Label(window, text="請輸入B").pack()
# 建立輸入框
entryB = tk.Entry(window)
entryB.pack()


# 用來顯示結果的 Label
result = tk.Label(window, text="")
result.pack()

def 計算():
    # entry.get() 會回傳目前輸入框裡的字串
    A = entryA.get()
    B = entryB.get()
    try:
        A =int(A)
        B = int(B)
        result.config(text=f"答案 = {A+B}")
    except:
        messagebox.showerror("媽的是不會打字?","傻逼")
        result.config(text=f"媽的是不會打字?") 
        pass  
    #print(f"數值A ={A} 數值B = {B}")
    # .config() 可以改變 Label 的設定
    

button = tk.Button(window, text="送出", command=計算)
button.pack()

window.mainloop()
