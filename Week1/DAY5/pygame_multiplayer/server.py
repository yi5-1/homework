# 多人小遊戲 - 伺服器端
# 責任：管理玩家 / 子彈 / 道具 / Buff / 聊天記錄，30Hz 廣播給所有 client
# 穩定性：每個 client 有獨立發送 queue，慢的 client 不會拖累其他人

import socket
import threading
import json
import time
import math
import random
import queue
import collections

from constants import (
    PORT, WORLD_W, WORLD_H, TICK_HZ,
    MAX_HP, PLAYER_SIZE,
    BULLET_SPEED, BULLET_LIFETIME, BULLET_RADIUS, BULLET_DAMAGE,
    SHOOT_COOLDOWN, SHOOT_COOLDOWN_RAPID,
    PICKUP_HEAL, PICKUP_RADIUS, PICKUP_MAX, PICKUP_SPAWN_INTERVAL,
    PICKUP_TYPES, PICKUP_WEIGHTS,
    HP_SIZE_BONUS, MAX_SIZE_BONUS,
    BUFF_DURATION,
    ORBIT_COUNT, ORBIT_RADIUS, ORBIT_ANGULAR_SPEED,
    ORBIT_HIT_DAMAGE, ORBIT_HIT_CD, ORBIT_BULLET_RADIUS,
    HOMING_TURN_RATE, HOMING_RANGE,
    CHAT_LOG_MAX,
    SUPER_REGEN, SUPER_REGEN_INTERVAL,
    KILL_FEED_MAX,
    MAX_LEVEL, XP_HP_PICKUP, XP_BUFF_PICKUP,
    LEVEL_HP_BONUS, LEVEL_DAMAGE_BONUS, xp_needed,
    BULLET_TIER_SPEED_BONUS,
)

HOST = "0.0.0.0"

# ====== 共享狀態 ======
players = {}   # {cid: player_dict}
bullets = []
pickups = []
chat_log = collections.deque(maxlen=CHAT_LOG_MAX)
kill_feed = collections.deque(maxlen=KILL_FEED_MAX)
lock = threading.Lock()

bullet_id_counter = 0
pickup_id_counter = 0

# (attacker_cid, victim_cid) -> next_hit_ts
orbit_hit_cd = {}


def 加擊殺公告(killer_p, victim_p, now):
    kill_feed.append({
        "killer":       killer_p["id"],
        "killer_color": killer_p["color"],
        "killer_super": killer_p.get("super", False),
        "victim":       victim_p["id"],
        "victim_color": victim_p["color"],
        "victim_super": victim_p.get("super", False),
        "ts":           now,
    })


class ClientConn:
    """每個 client 一個發送 queue + 發送 thread，慢的 client 不會阻塞廣播"""
    __slots__ = ("conn", "cid", "q", "alive")

    def __init__(self, conn, cid):
        self.conn = conn
        self.cid = cid
        self.q = queue.Queue(maxsize=8)
        self.alive = True

    def send(self, msg_bytes):
        try:
            self.q.put_nowait(msg_bytes)
        except queue.Full:
            # 慢客戶端：丟掉最舊的一筆，塞入最新
            try:
                self.q.get_nowait()
                self.q.put_nowait(msg_bytes)
            except queue.Empty:
                pass

    def sender_loop(self):
        while self.alive:
            msg = self.q.get()
            if msg is None:
                return
            try:
                self.conn.sendall(msg)
            except OSError:
                self.alive = False
                return

    def close(self):
        self.alive = False
        try:
            self.q.put_nowait(None)
        except queue.Full:
            pass
        try:
            self.conn.close()
        except OSError:
            pass


conns_by_cid = {}   # {cid: ClientConn}


def 隨機重生點():
    return random.randint(200, WORLD_W - 200), random.randint(200, WORLD_H - 200)


def 取得射擊冷卻(p, now):
    if p.get("rapid_forever") or now < p["buffs"].get("rapid", 0):
        return SHOOT_COOLDOWN_RAPID
    return SHOOT_COOLDOWN


def 套用道具(p, ptype, now):
    if ptype == "hp":
        p["hp"] = min(eff_max_hp(p), p["hp"] + PICKUP_HEAL)
        p["size_bonus"] = min(MAX_SIZE_BONUS, p["size_bonus"] + HP_SIZE_BONUS)
        加經驗(p, XP_HP_PICKUP, now)
    else:
        p["buffs"][ptype] = now + BUFF_DURATION
        加經驗(p, XP_BUFF_PICKUP, now)


def 玩家半徑(p):
    return PLAYER_SIZE + p.get("size_bonus", 0)


def eff_max_hp(p):
    return MAX_HP + (p.get("level", 1) - 1) * LEVEL_HP_BONUS


def eff_damage(p):
    return BULLET_DAMAGE + (p.get("level", 1) - 1) * LEVEL_DAMAGE_BONUS


def 加經驗(p, amount, now):
    if p["level"] >= MAX_LEVEL:
        return
    p["xp"] += amount
    while p["xp"] >= xp_needed(p["level"]) and p["level"] < MAX_LEVEL:
        p["xp"] -= xp_needed(p["level"])
        p["level"] += 1
        p["hp"] = eff_max_hp(p)      # 升級時補滿
        chat_log.append({
            "author": "系統",
            "text":   f"{p['id']} 升級到 Lv {p['level']}!",
            "ts":     now,
        })
    if p["level"] >= MAX_LEVEL:
        p["xp"] = 0


def 打包玩家(p, now):
    remaining = {k: max(0.0, v - now) for k, v in p.get("buffs", {}).items() if v > now}
    return {
        "id":         p["id"],
        "x":          p["x"],
        "y":          p["y"],
        "shape":      p["shape"],
        "color":      p["color"],
        "hp":         p["hp"],
        "alive":      p["alive"],
        "size_bonus": p.get("size_bonus", 0),
        "chat":       p.get("chat", ""),
        "chat_time":  p.get("chat_time", 0),
        "buffs":         remaining,
        "super":         p.get("super", False),
        "rapid_forever": p.get("rapid_forever", False),
        "speed_forever": p.get("speed_forever", False),
        "level":         p.get("level", 1),
        "xp":            p.get("xp", 0),
        "xp_need":       xp_needed(p.get("level", 1)) if p.get("level", 1) < MAX_LEVEL else 0,
        "max_hp":        eff_max_hp(p),
        "damage":        eff_damage(p),
    }


def 遊戲Tick():
    global bullet_id_counter, pickup_id_counter
    last = time.time()
    last_pickup_spawn = 0

    while True:
        now = time.time()
        dt = min(now - last, 0.1)  # 卡頓時不讓 dt 爆掉
        last = now

        with lock:
            # === 1) 追蹤子彈：轉向最近敵人 ===
            for b in bullets:
                if not b.get("homing"):
                    continue
                best = None
                best_d2 = HOMING_RANGE * HOMING_RANGE
                for cid, p in players.items():
                    if cid == b["owner"] or not p["alive"]:
                        continue
                    dx = p["x"] - b["x"]
                    dy = p["y"] - b["y"]
                    d2 = dx * dx + dy * dy
                    if d2 < best_d2:
                        best_d2 = d2
                        best = (dx, dy, math.sqrt(d2))
                if best:
                    dx, dy, d = best
                    tx, ty = dx / d, dy / d
                    speed = math.hypot(b["vx"], b["vy"])
                    if speed > 0:
                        cx, cy = b["vx"] / speed, b["vy"] / speed
                        cross = cx * ty - cy * tx  # >0 → 目標在左方，轉向逆時針
                        turn = HOMING_TURN_RATE * dt
                        turn = -turn if cross < 0 else turn
                        c, s = math.cos(turn), math.sin(turn)
                        b["vx"] = (cx * c - cy * s) * speed
                        b["vy"] = (cx * s + cy * c) * speed

            # === 2) 子彈移動 + 命中 ===
            for b in list(bullets):
                if now - b["t"] > BULLET_LIFETIME:
                    bullets.remove(b)
                    continue
                b["x"] += b["vx"] * dt
                b["y"] += b["vy"] * dt
                if b["x"] < 0 or b["x"] > WORLD_W or b["y"] < 0 or b["y"] > WORLD_H:
                    bullets.remove(b)
                    continue
                for cid, p in players.items():
                    if cid == b["owner"] or not p["alive"]:
                        continue
                    dx = p["x"] - b["x"]
                    dy = p["y"] - b["y"]
                    hitr = 玩家半徑(p) + BULLET_RADIUS
                    if dx * dx + dy * dy < hitr * hitr:
                        killer = players.get(b["owner"])
                        dmg = eff_damage(killer) if killer else BULLET_DAMAGE
                        p["hp"] -= dmg
                        if p["hp"] <= 0:
                            p["hp"] = 0
                            p["alive"] = False
                            if killer:
                                加擊殺公告(killer, p, now)
                        bullets.remove(b)
                        break

            # === 3) 軌道子彈（不存清單，每 tick 依角度即時算） ===
            orbit_snapshot = []
            for cid, p in players.items():
                if not p["alive"] or now >= p["buffs"].get("orbit", 0):
                    continue
                for i in range(ORBIT_COUNT):
                    ang = now * ORBIT_ANGULAR_SPEED + i * 2 * math.pi / ORBIT_COUNT
                    ox = p["x"] + math.cos(ang) * ORBIT_RADIUS
                    oy = p["y"] + math.sin(ang) * ORBIT_RADIUS
                    orbit_snapshot.append({
                        "owner_id": p["id"],
                        "color":    p["color"],
                        "x": ox, "y": oy,
                    })
                    # 命中判定
                    for vcid, vp in players.items():
                        if vcid == cid or not vp["alive"]:
                            continue
                        dx = vp["x"] - ox
                        dy = vp["y"] - oy
                        hitr = 玩家半徑(vp) + ORBIT_BULLET_RADIUS
                        if dx * dx + dy * dy < hitr * hitr:
                            key = (cid, vcid)
                            if orbit_hit_cd.get(key, 0) < now:
                                vp["hp"] -= ORBIT_HIT_DAMAGE
                                if vp["hp"] <= 0:
                                    vp["hp"] = 0
                                    vp["alive"] = False
                                    加擊殺公告(p, vp, now)
                                orbit_hit_cd[key] = now + ORBIT_HIT_CD

            # === 3.5) 金手指 auto-regen ===
            for p in players.values():
                if not p["alive"] or not p.get("super"):
                    continue
                if now - p.get("last_regen", 0) > SUPER_REGEN_INTERVAL:
                    p["hp"] = min(MAX_HP, p["hp"] + SUPER_REGEN)
                    p["last_regen"] = now

            # === 4) 生成道具 ===
            if now - last_pickup_spawn > PICKUP_SPAWN_INTERVAL and len(pickups) < PICKUP_MAX:
                pickup_id_counter += 1
                ptype = random.choices(PICKUP_TYPES, weights=PICKUP_WEIGHTS, k=1)[0]
                pickups.append({
                    "id":   pickup_id_counter,
                    "type": ptype,
                    "x":    random.randint(80, WORLD_W - 80),
                    "y":    random.randint(80, WORLD_H - 80),
                })
                last_pickup_spawn = now

            # === 5) 玩家撿道具 ===
            for p in players.values():
                if not p["alive"]:
                    continue
                for pk in list(pickups):
                    dx = p["x"] - pk["x"]
                    dy = p["y"] - pk["y"]
                    hitr = 玩家半徑(p) + PICKUP_RADIUS
                    if dx * dx + dy * dy < hitr * hitr:
                        套用道具(p, pk["type"], now)
                        pickups.remove(pk)

            # === 6) 打包狀態 ===
            state = {
                "type":     "state",
                "players":  [打包玩家(p, now) for p in players.values()],
                "bullets":  [{"x": b["x"], "y": b["y"], "homing": b.get("homing", False)} for b in bullets],
                "orbits":   orbit_snapshot,
                "pickups":  [{"x": pk["x"], "y": pk["y"], "type": pk["type"]} for pk in pickups],
                "chat_log":  list(chat_log),
                "kill_feed": list(kill_feed),
                "now":       now,
            }
            client_list = list(conns_by_cid.values())

        # === 7) 廣播（每個 client 自己的 queue，非同步） ===
        payload = (json.dumps(state) + "\n").encode("utf-8")
        for c in client_list:
            if c.alive:
                c.send(payload)

        time.sleep(1 / TICK_HZ)


def 處理單一連線(conn, cid, addr):
    global bullet_id_counter
    print(f"[{cid}] {addr} 已連線")
    cc = ClientConn(conn, cid)
    conns_by_cid[cid] = cc
    sender_thread = threading.Thread(target=cc.sender_loop, daemon=True)
    sender_thread.start()

    buf = b""
    try:
        while True:
            try:
                data = conn.recv(4096)
            except OSError:
                break
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                try:
                    msg = json.loads(line.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

                t = msg.get("type")
                now = time.time()
                with lock:
                    if t == "join":
                        x, y = 隨機重生點()
                        players[cid] = {
                            "id":         str(msg.get("id", f"P{cid}"))[:12],
                            "shape":      msg.get("shape", "circle"),
                            "color":      msg.get("color", [200, 50, 50]),
                            "x": x, "y": y,
                            "hp":         MAX_HP,
                            "alive":      True,
                            "size_bonus": 0,
                            "buffs":      {},
                            "chat": "", "chat_time": 0,
                            "shoot_cd_end": 0,
                            "super":         False,
                            "last_regen":    0,
                            "rapid_forever": False,
                            "speed_forever": False,
                            "level":         1,
                            "xp":            0,
                        }
                        print(f"[{cid}] 加入為 {players[cid]['id']}")

                    elif t == "update" and cid in players and players[cid]["alive"]:
                        players[cid]["x"] = max(0, min(WORLD_W, float(msg.get("x", 0))))
                        players[cid]["y"] = max(0, min(WORLD_H, float(msg.get("y", 0))))

                    elif t == "shoot" and cid in players and players[cid]["alive"]:
                        p = players[cid]
                        if now >= p["shoot_cd_end"]:
                            dx = float(msg.get("dx", 0))
                            dy = float(msg.get("dy", 0))
                            d = math.hypot(dx, dy)
                            if d > 0:
                                p["shoot_cd_end"] = now + 取得射擊冷卻(p, now)
                                tier = min(9, p["level"] // 10)
                                bspeed = BULLET_SPEED + BULLET_TIER_SPEED_BONUS[tier]
                                bullet_id_counter += 1
                                bullets.append({
                                    "id":      bullet_id_counter,
                                    "owner":   cid,
                                    "x":       p["x"],
                                    "y":       p["y"],
                                    "vx":      dx / d * bspeed,
                                    "vy":      dy / d * bspeed,
                                    "t":       now,
                                    "homing":  now < p["buffs"].get("homing", 0),
                                    "rainbow": p.get("super", False),
                                    "tier":    tier,
                                })

                    elif t == "chat" and cid in players:
                        p = players[cid]
                        txt = str(msg.get("text", ""))[:80].strip()
                        if txt == "/super":
                            if not p.get("super", False):
                                p["super"] = True
                                chat_log.append({
                                    "author": "系統",
                                    "text":   f"{p['id']} 開啟 金手指模式",
                                    "ts":     now,
                                })
                        elif txt == "/exitsuper":
                            if p.get("super", False):
                                p["super"] = False
                                chat_log.append({
                                    "author": "系統",
                                    "text":   f"{p['id']} 關閉 金手指模式",
                                    "ts":     now,
                                })
                        elif txt == "/快速射擊":
                            p["rapid_forever"] = not p.get("rapid_forever", False)
                            state_txt = "開啟" if p["rapid_forever"] else "關閉"
                            chat_log.append({
                                "author": "系統",
                                "text":   f"{p['id']} {state_txt} 快速射擊模式",
                                "ts":     now,
                            })
                        elif txt == "/跑快快":
                            p["speed_forever"] = True
                            chat_log.append({
                                "author": "系統",
                                "text":   f"{p['id']} 開啟 加速移動模式",
                                "ts":     now,
                            })
                        elif txt == "/跑慢慢":
                            p["speed_forever"] = False
                            chat_log.append({
                                "author": "系統",
                                "text":   f"{p['id']} 關閉 加速移動模式",
                                "ts":     now,
                            })
                        elif txt == "/變大":
                            p["size_bonus"] = MAX_SIZE_BONUS
                        elif txt == "/變小":
                            p["size_bonus"] = 0
                        elif txt:
                            p["chat"] = txt
                            p["chat_time"] = now
                            chat_log.append({"author": p["id"], "text": txt, "ts": now})

                    elif t == "respawn" and cid in players:
                        x, y = 隨機重生點()
                        p = players[cid]
                        p["hp"] = eff_max_hp(p)
                        p["alive"] = True
                        p["x"] = x
                        p["y"] = y
                        p["size_bonus"] = 0
                        p["buffs"].clear()
    finally:
        with lock:
            players.pop(cid, None)
            cc.close()
            conns_by_cid.pop(cid, None)
        print(f"[{cid}] 中斷連線")


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server 開啟於 {HOST}:{PORT}  (Ctrl+C 停止)")

    threading.Thread(target=遊戲Tick, daemon=True).start()

    cid_counter = 0
    try:
        while True:
            conn, addr = s.accept()
            # 提高即時性 + 偵測斷線
            try:
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            except OSError:
                pass
            cid_counter += 1
            threading.Thread(
                target=處理單一連線,
                args=(conn, cid_counter, addr),
                daemon=True,
            ).start()
    except KeyboardInterrupt:
        print("\nServer 關閉中...")
    finally:
        s.close()


if __name__ == "__main__":
    main()
