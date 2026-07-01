# 教學重點：grid() 用「橫列 row、直行 column」方式排版，像在排 Excel 表格
# 重要觀念：同一個視窗裡 pack 和 grid 不能混用！

import tkinter as tk

window = tk.Tk()
window.title("grid 排版練習")
window.geometry("400x300")

# row = 第幾列（從 0 開始，0 是最上面）
# column = 第幾行（從 0 開始，0 是最左邊）
tk.Label(window, text="姓名：").grid(row=0, column=0, padx=5, pady=5)
tk.Entry(window).grid(row=0, column=1, padx=5, pady=5)

tk.Label(window, text="電話：").grid(row=1, column=0, padx=5, pady=5)
tk.Entry(window).grid(row=1, column=1, padx=5, pady=5)

tk.Label(window, text="地址：").grid(row=2, column=0, padx=5, pady=5)
tk.Entry(window).grid(row=2, column=1, padx=5, pady=5)

# columnspan=2 代表這個元件橫跨 2 行
tk.Button(window, text="送出").grid(row=3, column=0, columnspan=2, pady=10)

window.mainloop()
