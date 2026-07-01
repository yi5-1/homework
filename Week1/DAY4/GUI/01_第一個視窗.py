# 教學重點：建立一個最基本的視窗
# tkinter 是 Python 內建的 GUI 套件，不用 pip install

import tkinter as tk

# Tk() 就是「建立一個視窗」
window = tk.Tk()

# 設定視窗標題（最上面那條藍藍的字）
window.title("我的刀盾")

# 設定視窗大小，格式：'寬x高'，注意中間是英文字母 x 不是乘號
window.geometry("1920x1080")

# mainloop() 讓視窗保持開啟，不寫的話視窗會一閃就關掉
window.mainloop()
