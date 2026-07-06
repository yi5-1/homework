# 客戶端入口：Lobby (選 IP/ID/造型/顏色) → 連線 → 進入遊戲
# 用法：python client.py

import socket
import json

import pygame

from constants import PORT
from lobby import show_lobby
from game  import run_game


def main():
    # 1) 大廳
    config = show_lobby()
    if config is None:
        pygame.quit()
        return

    # 2) 連線（TCP_NODELAY 降低延遲、SO_KEEPALIVE 偵測斷線）
    sock = socket.socket()
    try:
        sock.connect((config["ip"], PORT))
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    except OSError as e:
        print(f"連線失敗：{e}")
        pygame.quit()
        return

    # 3) 送出 join
    join = {
        "type":  "join",
        "id":    config["id"],
        "shape": config["shape"],
        "color": config["color"],
    }
    try:
        sock.sendall((json.dumps(join) + "\n").encode("utf-8"))
    except OSError as e:
        print(f"傳送 join 失敗：{e}")
        pygame.quit()
        sock.close()
        return

    # 4) 進入遊戲
    try:
        run_game(sock, config)
    finally:
        try:
            sock.close()
        except OSError:
            pass
        pygame.quit()


if __name__ == "__main__":
    main()
