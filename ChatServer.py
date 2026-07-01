import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

client_names = {}
server_running = False
server_socket = None

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

def broadcast(message, current_client):
    for client in list(client_names.keys()):
        if client != current_client:
            try:
                client.send(message)
            except:
                remove_client(client)

def remove_client(client_socket):
    if client_socket in client_names:
        username = client_names[client_socket]
        del client_names[client_socket]
        try:
            client_socket.close()
        except:
            pass
        root.after(0, log, f"[斷線] {username} 已離開。")
        leave_msg = f"【系統】使用者 [{username}] 離開了聊天室。\n".encode('utf-8')
        broadcast(leave_msg, client_socket)
        root.after(0, update_client_list)

def handle_client(client_socket, client_address):
    username = "未知用戶"
    try:
        username = client_socket.recv(1024).decode('utf-8').strip()
        if not username:
            username = f"User_{client_address[1]}"
        client_names[client_socket] = username
        root.after(0, log, f"[新連線] {client_address} 已註冊暱稱: {username}")
        root.after(0, update_client_list)
        welcome_msg = f"【系統】使用者 [{username}] 進入了聊天室。\n".encode('utf-8')
        broadcast(welcome_msg, client_socket)
        while True:
            message = client_socket.recv(1024)
            if not message:
                break
            formatted_msg = f"[{username}]: ".encode('utf-8') + message
            broadcast(formatted_msg, client_socket)
    except:
        pass
    finally:
        remove_client(client_socket)

def log(msg):
    log_area.config(state=tk.NORMAL)
    if "新連線" in msg:
        log_area.insert(tk.END, msg + "\n", "connect")
    elif "斷線" in msg:
        log_area.insert(tk.END, msg + "\n", "disconnect")
    else:
        log_area.insert(tk.END, msg + "\n", "normal")
    log_area.see(tk.END)
    log_area.config(state=tk.DISABLED)

def update_client_list():
    client_listbox.delete(0, tk.END)
    for name in client_names.values():
        client_listbox.insert(tk.END, f"  ⚔ {name}")

def start_server():
    global server_running, server_socket
    if server_running:
        messagebox.showinfo("提示", "伺服器已在執行中")
        return
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('127.0.0.1', 12345))
        server_socket.settimeout(1.0)
        server_socket.listen()
        server_running = True
        start_btn.config(text="🛑 停止", command=stop_server, bg=C_RED, fg=C_BG)
        status_label.config(text="● 伺服器執行中", fg=C_GREEN)
        log("[啟動] 聊天室 Server 已啟動，等待連線...")
        threading.Thread(target=accept_clients, daemon=True).start()
    except Exception as e:
        messagebox.showerror("錯誤", f"無法啟動伺服器: {e}")

def stop_server():
    global server_running, server_socket
    if not server_running:
        return
    server_running = False
    for client in list(client_names.keys()):
        try:
            client.close()
        except:
            pass
    client_names.clear()
    if server_socket:
        try:
            server_socket.close()
        except:
            pass
    start_btn.config(text="▶ 啟動", command=start_server, bg=C_GREEN, fg=C_BG)
    status_label.config(text="● 已停止", fg=C_RED)
    update_client_list()
    log("[停止] 伺服器已關閉。")

def accept_clients():
    global server_socket
    while server_running:
        try:
            client_socket, client_address = server_socket.accept()
            threading.Thread(target=handle_client, args=(client_socket, client_address), daemon=True).start()
        except socket.timeout:
            continue
        except:
            break

def on_closing():
    stop_server()
    root.destroy()

root = tk.Tk()
root.title("伺服器管理")
root.geometry("640x500")
root.configure(bg=C_BG)
root.protocol("WM_DELETE_WINDOW", on_closing)

main_frame = tk.Frame(root, bg=C_BG, padx=10, pady=10)
main_frame.pack(fill=tk.BOTH, expand=True)

top_frame = tk.Frame(main_frame, bg=C_BG2, padx=10, pady=8)
top_frame.pack(fill=tk.X, pady=(0, 10))

tk.Label(top_frame, text="⚔ 聊天室 ⚔", font=FONT_TITLE,
         fg=C_GOLD, bg=C_BG2).pack(side=tk.LEFT)

status_label = tk.Label(top_frame, text="● 已停止", font=FONT_BOLD,
                        fg=C_RED, bg=C_BG2)
status_label.pack(side=tk.RIGHT)

btn_frame = tk.Frame(main_frame, bg=C_BG)
btn_frame.pack(fill=tk.X, pady=(0, 10))

start_btn = tk.Button(btn_frame, text="▶ 啟動", command=start_server,
                      font=FONT_BOLD, bg=C_GREEN, fg=C_BG,
                      activebackground=C_CYAN, activeforeground=C_BG,
                      relief=tk.RAISED, bd=3, cursor="hand2", width=12)
start_btn.pack(side=tk.LEFT)

tk.Label(btn_frame, text=f"Port: 12345", font=FONT,
         fg=C_DIM, bg=C_BG).pack(side=tk.LEFT, padx=15)

content_frame = tk.Frame(main_frame, bg=C_BG)
content_frame.pack(fill=tk.BOTH, expand=True)

log_frame = tk.LabelFrame(content_frame, text=" 伺服器日誌 ", font=FONT_BOLD,
                          fg=C_GOLD, bg=C_BG, padx=5, pady=5, bd=1,
                          highlightbackground=C_BG3, highlightcolor=C_BG3,
                          highlightthickness=1)
log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

log_area = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED,
                                     font=FONT_SM, bg=C_BG2, fg=C_TEXT,
                                     relief=tk.FLAT, bd=3, padx=6, pady=6,
                                     highlightthickness=1,
                                     highlightbackground=C_BG3)
log_area.pack(fill=tk.BOTH, expand=True)

log_area.tag_config("connect", foreground=C_GREEN)
log_area.tag_config("disconnect", foreground=C_RED)
log_area.tag_config("normal", foreground=C_TEXT)

clients_frame = tk.LabelFrame(content_frame, text=" 連線用戶 ", font=FONT_BOLD,
                              fg=C_CYAN, bg=C_BG, padx=5, pady=5, bd=1,
                              highlightbackground=C_BG3, highlightcolor=C_BG3,
                              highlightthickness=1)
clients_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

client_listbox = tk.Listbox(clients_frame, font=FONT, bg=C_BG2, fg=C_TEXT,
                            relief=tk.FLAT, bd=3, highlightthickness=0,
                            selectbackground=C_BG3, width=22)
client_listbox.pack(fill=tk.BOTH, expand=True)

root.mainloop()
