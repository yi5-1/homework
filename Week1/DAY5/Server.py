# server.py
import socket

# 1. 建立 socket 物件
# AF_INET 表示使用 IPv4，SOCK_STREAM 表示使用 TCP 協定
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 2. 綁定 IP 與 Port ('' 代表監聽本機所有網路介面，例如 localhost)
server_socket.bind(('127.0.0.1', 12345))

# 3. 開始監聽 (參數 1 表示排隊等待連線的最大數量)
server_socket.listen(1)
print("Server 啟動，等待 Client 連線...")

# 4. 接受 Client 連線 (程式會在這裡阻塞，直到有人連進來)
client_socket, client_address = server_socket.accept()
print(head_msg := f"已成功與 {client_address} 建立連線！")

# 5. 接收 Client 傳來的訊息 (最多接收 1024 位元組)
# 網路傳輸必須是 bytes，所以收到後要用 utf-8 解碼成字串
data = client_socket.recv(1024).decode('utf-8')
print(f"收到 Client 訊息: {data}")

# 6. 回應訊息給 Client (必須先編碼成 bytes)
response_msg = "哈囉 Client！我已經收到你的訊息了。"
client_socket.send(response_msg.encode('utf-8'))

# 7. 關閉連線
client_socket.close()
server_socket.close()
print("Server 已關閉。")