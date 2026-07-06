# client_chat.py
import socket
import threading
import sys

def receive_messages(client_socket):
    """專職接收來自 Server 的訊息"""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                # 清除目前輸入行的提示，印出新訊息，再補上「你: 」
                sys.stdout.write('\r' + message + '\n你: ')
                sys.stdout.flush()
            else:
                print("\n[系統] 與伺服器中斷連線。")
                break
        except:
            print("\n[系統] 發生錯誤，連線關閉。")
            break
    client_socket.close()

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('192.168.1.101', 12345))
        print("[成功] 已連線至聊天室伺服器！")
    except Exception as e:
        print(f"[失敗] 無法連線至伺服器: {e}")
        return

    # 【關鍵步驟 1】一連線成功，先要求輸入使用者名稱
    username = input("請輸入你的使用者名稱 (Username): ").strip()
    while not username:
        username = input("名稱不能為空，請重新輸入: ").strip()
        
    # 將名字送給 Server 進行註冊
    client.send(username.encode('utf-8'))
    print(f"--- 歡迎 [{username}] 進入聊天室，開始聊天吧！ ---")

    # 【關鍵步驟 2】開啟執行緒專門用來「接收訊息」
    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.daemon = True
    receive_thread.start()

    # 主執行緒負責「發送訊息」
    while True:
        try:
            msg = input("你: ")
            if msg.strip() == "":
                continue
            client.send(msg.encode('utf-8'))
        except (KeyboardInterrupt, EOFError):
            print("\n[系統] 正在離開聊天室...")
            break

    client.close()

if __name__ == "__main__":
    start_client()