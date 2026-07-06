# server_chat.py
import socket
import threading

# 使用字典儲存 { client_socket: username }
client_names = {}

def broadcast(message, current_client):
    """將訊息轉發給其他所有人（排除發送者自己）"""
    for client in client_names:
        if client != current_client:
            try:
                client.send(message)
            except:
                remove_client(client)

def handle_client(client_socket, client_address):
    """處理單一 Client 的通訊流程"""
    username = "未知用戶"
    try:
        # 【關鍵步驟 1】Client 連線後發送的第一筆訊息，規定為使用者名稱
        username = client_socket.recv(1024).decode('utf-8').strip()
        if not username:
            username = f"User_{client_address[1]}" # 如果沒輸入就用 Port 號暫代
            
        # 記錄到字典中
        client_names[client_socket] = username
        print(f"[新連線] {client_address} 已註冊暱稱: {username}")
        
        # 廣播給其他人：某人加入了聊天室
        welcome_msg = f"【系統】使用者 [{username}] 進入了聊天室。\n".encode('utf-8')
        broadcast(welcome_msg, client_socket)

        # 【關鍵步驟 2】開始常駐接收該用戶的聊天訊息
        while True:
            message = client_socket.recv(1024)
            if not message:
                break
            
            # 格式化訊息：加上發送者的名字
            formatted_msg = f"[{username}]: ".encode('utf-8') + message
            broadcast(formatted_msg, client_socket)
            
    except Exception as e:
        print(f"[錯誤] 處理 {username} 的連線時發生異常: {e}")

    # 當跳出迴圈（斷線或出錯），清理連線
    remove_client(client_socket)

def remove_client(client_socket):
    """移除斷線的 Client"""
    if client_socket in client_names:
        username = client_names[client_socket]
        del client_names[client_socket]
        client_socket.close()
        
        print(f"[斷線] {username} 已離開。")
        leave_msg = f"【系統】使用者 [{username}] 離開了聊天室。\n".encode('utf-8')
        broadcast(leave_msg, client_socket)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 12345))
    server.listen()
    print("[啟動] 聊天室 Server 正在執行，等待連線...")

    while True:
        client_socket, client_address = server.accept()
        # 收到新連線後，直接交給執行緒處理（暱稱輸入會在執行緒內處理）
        thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    start_server()