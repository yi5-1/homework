import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

client_socket = None
connected = False
username = ""

C_BG = "#0f0f1a"
C_BG2 = "#1a1a2e"
C_BG3 = "#252540"
C_GOLD = "#e8b828"
C_CYAN = "#4fc3f7"
C_GREEN = "#4caf50"
C_TEXT = "#e0e0e0"
C_DIM = "#888899"
C_RED = "#ef5350"
FONT = ("Consolas", 11)
FONT_BOLD = ("Consolas", 11, "bold")
FONT_TITLE = ("Consolas", 14, "bold")
FONT_SM = ("Consolas", 9)

def receive_messages():
    global connected
    while connected:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                root.after(0, display_message, message)
            else:
                root.after(0, on_disconnect)
                break
        except:
            if connected:
                root.after(0, on_disconnect)
            break

def display_message(msg):
    chat_area.config(state=tk.NORMAL)
    if msg.startswith("【系統】"):
        chat_area.insert(tk.END, msg + "\n", "system")
    elif ":" in msg:
        sender, rest = msg.split(":", 1)
        chat_area.insert(tk.END, sender + ":", "sender")
        chat_area.insert(tk.END, rest + "\n", "normal")
    else:
        chat_area.insert(tk.END, msg + "\n", "normal")
    chat_area.see(tk.END)
    chat_area.config(state=tk.DISABLED)

def on_disconnect():
    global connected
    connected = False
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, "[系統] 與伺服器中斷連線。\n", "system")
    chat_area.config(state=tk.DISABLED)
    send_btn.config(state=tk.DISABLED, bg=C_BG3, fg=C_DIM)
    msg_entry.config(state=tk.DISABLED, bg=C_BG3, fg=C_DIM)

def send_message(event=None):
    msg = msg_entry.get().strip()
    if not msg:
        return
    try:
        client_socket.send(msg.encode('utf-8'))
        display_message(f"[{username}]: {msg}")
        msg_entry.delete(0, tk.END)
    except:
        messagebox.showerror("錯誤", "無法發送訊息，請檢查連線。")

def connect_to_server():
    global client_socket, connected, username
    username = username_entry.get().strip()
    if not username:
        messagebox.showwarning("提示", "請輸入使用者名稱")
        return
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5.0)
        client_socket.connect(('127.0.0.1', 12345))
        client_socket.settimeout(None)
        client_socket.send(username.encode('utf-8'))
        connected = True
        root.title(f"聊天室 - {username}")
        login_frame.pack_forget()
        chat_frame.pack(fill=tk.BOTH, expand=True)
        threading.Thread(target=receive_messages, daemon=True).start()
        display_message(f"--- 歡迎 [{username}] 進入聊天室，開始聊天吧！ ---")
    except Exception as e:
        messagebox.showerror("連線失敗", f"無法連線至伺服器: {e}")

def on_closing():
    global connected
    connected = False
    if client_socket:
        try:
            client_socket.close()
        except:
            pass
    root.destroy()

root = tk.Tk()
root.title("聊天室")
root.geometry("560x500")
root.configure(bg=C_BG)
root.protocol("WM_DELETE_WINDOW", on_closing)

login_frame = tk.Frame(root, bg=C_BG)
login_frame.pack(fill=tk.BOTH, expand=True)

tk.Label(login_frame, text="⚔ 連線至伺服器 ⚔", font=FONT_TITLE,
         fg=C_GOLD, bg=C_BG).pack(pady=(50, 30))

tk.Frame(login_frame, height=2, bg=C_GOLD).pack(fill=tk.X, padx=80)

tk.Label(login_frame, text="請輸入名稱", font=FONT, fg=C_CYAN, bg=C_BG).pack(pady=(20, 5))
username_entry = tk.Entry(login_frame, width=28, font=FONT,
                          bg=C_BG2, fg=C_TEXT, insertbackground=C_GOLD,
                          relief=tk.FLAT, bd=8, highlightthickness=1,
                          highlightbackground=C_GOLD, highlightcolor=C_GOLD)
username_entry.pack(pady=(0, 15), ipady=4)
username_entry.focus_set()
username_entry.bind("<Return>", lambda e: connect_to_server())

connect_btn = tk.Button(login_frame, text="進 入 聊 天 室", command=connect_to_server,
                        font=FONT_BOLD, bg=C_GOLD, fg=C_BG, activebackground=C_CYAN,
                        activeforeground=C_BG, relief=tk.RAISED, bd=3, cursor="hand2",
                        width=18, height=1)
connect_btn.pack(pady=(10, 0))

tk.Label(login_frame, text="伺服器: 127.0.0.1:12345", font=FONT_SM,
         fg=C_DIM, bg=C_BG).pack(pady=(40, 0))

chat_frame = tk.Frame(root, bg=C_BG)

header = tk.Frame(chat_frame, bg=C_BG2, height=40)
header.pack(fill=tk.X, pady=(0, 5))
tk.Label(header, text="✦ 聊 天 室 ✦", font=FONT_TITLE,
         fg=C_GOLD, bg=C_BG2).pack(pady=8)

chat_area = scrolledtext.ScrolledText(chat_frame, state=tk.DISABLED,
                                      font=FONT, bg=C_BG2, fg=C_TEXT,
                                      insertbackground=C_GOLD,
                                      relief=tk.FLAT, bd=5, padx=8, pady=8,
                                      highlightthickness=1,
                                      highlightbackground=C_BG3,
                                      highlightcolor=C_GOLD)
chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

chat_area.tag_config("system", foreground=C_GOLD, font=FONT_BOLD)
chat_area.tag_config("sender", foreground=C_CYAN, font=FONT_BOLD)
chat_area.tag_config("normal", foreground=C_TEXT)

input_frame = tk.Frame(chat_frame, bg=C_BG)
input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

msg_entry = tk.Entry(input_frame, font=FONT, bg=C_BG2, fg=C_TEXT,
                     insertbackground=C_GOLD, relief=tk.FLAT, bd=8,
                     highlightthickness=1, highlightbackground=C_BG3,
                     highlightcolor=C_GOLD)
msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=4)
msg_entry.bind("<Return>", send_message)

send_btn = tk.Button(input_frame, text="發送 ⏎", command=send_message,
                     font=FONT_BOLD, bg=C_GOLD, fg=C_BG,
                     activebackground=C_CYAN, activeforeground=C_BG,
                     relief=tk.RAISED, bd=3, cursor="hand2", width=8)
send_btn.pack(side=tk.RIGHT)

status_bar = tk.Frame(chat_frame, bg=C_BG, height=22)
status_bar.pack(fill=tk.X, padx=5, pady=(0, 5))
tk.Label(status_bar, text="連線中 ...", font=FONT_SM,
         fg=C_GREEN, bg=C_BG).pack(side=tk.LEFT)

root.mainloop()
