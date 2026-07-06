# client.py
import socket

# 1. 建立 socket 物件
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 2. 連線到 Server 的 IP 與 Port
print("正在連線到 Server...")
client_socket.connect(('127.0.0.1', 12345))

# 3. 發送訊息給 Server (記得要編碼成 bytes)
send_msg = "你好 Server，這是一條測試訊息！"
client_socket.send(send_msg.encode('utf-8'))

# 4. 接收 Server 的回應
server_reply = client_socket.recv(1024).decode('utf-8')
print(f"收到 Server 回應: {server_reply}")

# 5. 關閉連線
client_socket.close()
print("Client 已關閉。")