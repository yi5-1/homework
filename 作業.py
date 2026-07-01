import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import socket
import threading

SERVER = None
clients = []
server_running = False

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return socket.gethostbyname(socket.gethostname())

def start_server():
    global SERVER, server_running
    if server_running:
        messagebox.showwarning("警告", "伺服器已經在運行")
        return
    port = simpledialog.askinteger("設定伺服器", "請輸入連接埠號碼：", minvalue=1024, maxvalue=65535)
    if not port:
        return
    try:
        SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SERVER.bind(('0.0.0.0', port))
        SERVER.listen(5)
        server_running = True
        start_btn.config(state='disabled')
        stop_btn.config(state='normal')
        ip = get_local_ip()
        messagebox.showinfo("成功", f"伺服器已啟動\nIP: {ip}\nPort: {port}\n\n其他電腦請連線到此 IP")
        threading.Thread(target=accept_clients, args=(port,), daemon=True).start()
    except Exception as e:
        messagebox.showerror("錯誤", f"啟動伺服器失敗：{e}")
        server_running = False

def accept_clients(port):
    global server_running
    while server_running:
        try:
            SERVER.settimeout(1.0)
            client, addr = SERVER.accept()
            clients.append(client)
            threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()
        except socket.timeout:
            continue
        except:
            break

def handle_client(client, addr):
    broadcast(f"[系統] {addr[0]}:{addr[1]} 已加入聊天室".encode('utf-8'), client)
    while True:
        try:
            msg = client.recv(4096)
            if not msg:
                break
            broadcast(msg, client)
        except:
            break
    clients.remove(client)
    client.close()
    broadcast(f"[系統] {addr[0]}:{addr[1]} 已離開聊天室".encode('utf-8'), None)

def broadcast(msg, sender=None):
    for c in clients[:]:
        try:
            if c != sender:
                c.send(msg)
        except:
            clients.remove(c)

class ChatClient:
    def __init__(self, sock, name):
        self.sock = sock
        self.name = name
        self.window = tk.Toplevel()
        self.window.title(f"聊天室 - {name}")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.text_area = scrolledtext.ScrolledText(self.window, state='disabled', height=20, width=60)
        self.text_area.pack(padx=10, pady=10)

        frame = tk.Frame(self.window)
        frame.pack(padx=10, pady=(0, 10), fill='x')

        self.entry = tk.Entry(frame)
        self.entry.pack(side='left', fill='x', expand=True)
        self.entry.bind('<Return>', lambda e: self.send_msg())

        self.send_btn = tk.Button(frame, text="發送", command=self.send_msg)
        self.send_btn.pack(side='right', padx=(5, 0))

        self.running = True
        threading.Thread(target=self.receive_loop, daemon=True).start()

    def send_msg(self):
        text = self.entry.get().strip()
        if not text:
            return
        try:
            self.sock.send(f"{self.name}: {text}".encode('utf-8'))
            self.entry.delete(0, 'end')
        except:
            messagebox.showerror("錯誤", "無法發送訊息")
            self.on_close()

    def receive_loop(self):
        while self.running:
            try:
                msg = self.sock.recv(4096)
                if not msg:
                    break
                text = msg.decode('utf-8')
                self.window.after(0, self.display_msg, text)
            except:
                break
        self.window.after(0, self.on_close)

    def display_msg(self, text):
        self.text_area.configure(state='normal')
        self.text_area.insert('end', text + '\n')
        self.text_area.see('end')
        self.text_area.configure(state='disabled')

    def on_close(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        try:
            self.window.destroy()
        except:
            pass

def connect_server():
    host = simpledialog.askstring("連線到伺服器", "請輸入伺服器 IP：", initialvalue="127.0.0.1")
    if not host:
        return
    port = simpledialog.askinteger("連線到伺服器", "請輸入連接埠號碼：", minvalue=1, maxvalue=65535)
    if not port:
        return
    name = simpledialog.askstring("連線到伺服器", "請輸入你的暱稱：")
    if not name:
        return
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.send(f"[系統] {name} 已加入聊天室".encode('utf-8'))
        ChatClient(sock, name)
    except Exception as e:
        messagebox.showerror("錯誤", f"連線失敗：{e}")

def stop_server():
    global SERVER, server_running
    if not server_running:
        return
    server_running = False
    for c in clients[:]:
        try:
            c.close()
        except:
            pass
    clients.clear()
    try:
        SERVER.close()
    except:
        pass
    SERVER = None
    stop_btn.config(state='disabled')
    start_btn.config(state='normal')
    messagebox.showinfo("已關閉", "伺服器已關閉")

def main():
    root = tk.Tk()
    root.title("聊天室")
    root.geometry("300x220")

    tk.Label(root, text="區域網路聊天室", font=("Arial", 16)).pack(pady=20)

    global start_btn, stop_btn
    start_btn = tk.Button(root, text="設定伺服器", command=start_server, width=20, height=2)
    start_btn.pack(pady=5)
    stop_btn = tk.Button(root, text="關閉伺服器", command=stop_server, width=20, height=2, state='disabled')
    stop_btn.pack(pady=5)
    tk.Button(root, text="連線到伺服器", command=connect_server, width=20, height=2).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
