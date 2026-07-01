# 教學重點：pack() 的方向參數 side
# 重要觀念：side 可以指定 'top'(預設) / 'bottom' / 'left' / 'right'

import tkinter as tk

window = tk.Tk()
window.title("pack 排版練習")
window.geometry("600x600")

# 沒寫 side，預設由上往下排
tk.Label(window, text="我在最上面", bg="lightblue").pack(side="top")

# 貼到下面
tk.Label(window, text="我在最下面", bg="lightgreen").pack(side="bottom")

# 貼到左邊
tk.Label(window, text="我在左邊", bg="pink").pack(side="left")

# 貼到右邊
tk.Label(window, text="我在右邊", bg="orange").pack(side="right")

# padx / pady 可以加上左右 / 上下的留白
tk.Label(window, text="我有留白", bg="yellow").pack(pady=20, padx=20)

window.mainloop()
