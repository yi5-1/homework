# Web 多人射擊 - aiohttp server
# 同一個 process 服務 HTTP (靜態檔) + WebSocket (遊戲)
# 用法：python server.py  → 瀏覽器打開 http://<ip>:8080/

import asyncio
import json
import time
import math
import random
import collections
from pathlib import Path

from aiohttp import web, WSMsgType

from constants import (
    PORT, WORLD_W, WORLD_H, TICK_HZ,
    PLAYER_SIZE, MAX_HP,
    BULLET_SPEED, BULLET_LIFETIME, BULLET_RADIUS, BULLET_DAMAGE,
    SHOOT_COOLDOWN, SHOOT_COOLDOWN_RAPID,
    PICKUP_HEAL, PICKUP_RADIUS, PICKUP_MAX, PICKUP_SPAWN_INTERVAL,
    PICKUP_TYPES, PICKUP_WEIGHTS,
    HP_SIZE_BONUS, MAX_SIZE_BONUS,
    BUFF_DURATION,
    ORBIT_COUNT, ORBIT_RADIUS, ORBIT_ANGULAR_SPEED,
    ORBIT_HIT_DAMAGE, ORBIT_HIT_CD, ORBIT_BULLET_RADIUS,
    HOMING_TURN_RATE, HOMING_RANGE,
    CHAT_LOG_MAX, KILL_FEED_MAX,
    SUPER_REGEN, SUPER_REGEN_INTERVAL,
    MAX_LEVEL, XP_HP_PICKUP, XP_BUFF_PICKUP,
    LEVEL_HP_BONUS, LEVEL_DAMAGE_BONUS, xp_needed,
    BULLET_TIER_SPEED_BONUS,
)

STATIC_DIR = Path(__file__).parent / "static"

# ====== 遊戲狀態（單一 event loop, 不需要 lock）======
players = {}      # cid -> player dict
bullets = []
pickups = []
chat_log  = collections.deque(maxlen=CHAT_LOG_MAX)
kill_feed = collections.deque(maxlen=KILL_FEED_MAX)
orbit_hit_cd = {}
ws_of_cid = {}    # cid -> WebSocketResponse
next_cid = 0
bullet_id_counter = 0
pickup_id_counter = 0


def 隨機重生點():
    return random.randint(200, WORLD_W - 200), random.randint(200, WORLD_H - 200)


def 玩家半徑(p):
    return PLAYER_SIZE + p.get("size_bonus", 0)


def eff_max_hp(p):
    return MAX_HP + (p.get("level", 1) - 1) * LEVEL_HP_BONUS


def eff_damage(p):
    return BULLET_DAMAGE + (p.get("level", 1) - 1) * LEVEL_DAMAGE_BONUS


def 取得射擊冷卻(p, now):
    if p.get("rapid_forever") or now < p["buffs"].get("rapid", 0):
        return SHOOT_COOLDOWN_RAPID
    return SHOOT_COOLDOWN


def 加經驗(p, amount, now):
    if p["level"] >= MAX_LEVEL:
        return
    p["xp"] += amount
    while p["xp"] >= xp_needed(p["level"]) and p["level"] < MAX_LEVEL:
        p["xp"] -= xp_needed(p["level"])
        p["level"] += 1
        p["hp"] = eff_max_hp(p)
        chat_log.append({
            "author": "系統",
            "text":   f"{p['id']} 升級到 Lv {p['level']}!",
            "ts":     now,
        })
    if p["level"] >= MAX_LEVEL:
        p["xp"] = 0


def 套用道具(p, ptype, now):
    if ptype == "hp":
        p["hp"] = min(eff_max_hp(p), p["hp"] + PICKUP_HEAL)
        p["size_bonus"] = min(MAX_SIZE_BONUS, p["size_bonus"] + HP_SIZE_BONUS)
        加經驗(p, XP_HP_PICKUP, now)
    else:
        p["buffs"][ptype] = now + BUFF_DURATION
        加經驗(p, XP_BUFF_PICKUP, now)


def 加擊殺公告(killer, victim, now):
    kill_feed.append({
        "killer":       killer["id"],
        "killer_color": killer["color"],
        "killer_super": killer.get("super", False),
        "victim":       victim["id"],
        "victim_color": victim["color"],
        "victim_super": victim.get("super", False),
        "ts":           now,
    })


def 打包玩家(p, now):
    remaining = {k: max(0.0, v - now) for k, v in p.get("buffs", {}).items() if v > now}
    lvl = p.get("level", 1)
    return {
        "id":            p["id"],
        "x":             p["x"],
        "y":             p["y"],
        "shape":         p["shape"],
        "color":         p["color"],
        "hp":            p["hp"],
        "alive":         p["alive"],
        "size_bonus":    p.get("size_bonus", 0),
        "chat":          p.get("chat", ""),
        "chat_time":     p.get("chat_time", 0),
        "buffs":         remaining,
        "super":         p.get("super", False),
        "rapid_forever": p.get("rapid_forever", False),
        "speed_forever": p.get("speed_forever", False),
        "level":         lvl,
        "xp":            p.get("xp", 0),
        "xp_need":       xp_needed(lvl) if lvl < MAX_LEVEL else 0,
        "max_hp":        eff_max_hp(p),
        "damage":        eff_damage(p),
    }


# ====== 訊息處理 ======
async def 處理訊息(cid, msg):
    global bullet_id_counter
    t = msg.get("type")
    now = time.time()

    if t == "join":
        x, y = 隨機重生點()
        players[cid] = {
            "id":            str(msg.get("id", f"P{cid}"))[:12],
            "shape":         msg.get("shape", "circle"),
            "color":         msg.get("color", [200, 50, 50]),
            "x": x, "y": y,
            "hp":            MAX_HP,
            "alive":         True,
            "size_bonus":    0,
            "buffs":         {},
            "chat": "", "chat_time": 0,
            "shoot_cd_end":  0,
            "super":         False,
            "last_regen":    0,
            "rapid_forever": False,
            "speed_forever": False,
            "level":         1,
            "xp":            0,
        }
        print(f"[{cid}] 加入為 {players[cid]['id']}")

    elif t == "update" and cid in players and players[cid]["alive"]:
        p = players[cid]
        p["x"] = max(0, min(WORLD_W, float(msg.get("x", 0))))
        p["y"] = max(0, min(WORLD_H, float(msg.get("y", 0))))

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
            if not p.get("super"):
                p["super"] = True
                chat_log.append({"author": "系統", "text": f"{p['id']} 開啟 金手指模式", "ts": now})
        elif txt == "/exitsuper":
            if p.get("super"):
                p["super"] = False
                chat_log.append({"author": "系統", "text": f"{p['id']} 關閉 金手指模式", "ts": now})
        elif txt == "/快速射擊":
            p["rapid_forever"] = not p.get("rapid_forever", False)
            state_txt = "開啟" if p["rapid_forever"] else "關閉"
            chat_log.append({"author": "系統", "text": f"{p['id']} {state_txt} 快速射擊模式", "ts": now})
        elif txt == "/跑快快":
            p["speed_forever"] = True
            chat_log.append({"author": "系統", "text": f"{p['id']} 開啟 加速移動模式", "ts": now})
        elif txt == "/跑慢慢":
            p["speed_forever"] = False
            chat_log.append({"author": "系統", "text": f"{p['id']} 關閉 加速移動模式", "ts": now})
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


# ====== WebSocket handler ======
async def ws_handler(request):
    global next_cid
    ws = web.WebSocketResponse(heartbeat=15)
    await ws.prepare(request)
    next_cid += 1
    cid = next_cid
    ws_of_cid[cid] = ws
    print(f"[{cid}] {request.remote} 已連線")
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue
                await 處理訊息(cid, data)
            elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                break
    finally:
        players.pop(cid, None)
        ws_of_cid.pop(cid, None)
        print(f"[{cid}] 中斷連線")
    return ws


# ====== 遊戲 tick ======
async def 遊戲Tick():
    global pickup_id_counter
    last = time.time()
    last_pickup_spawn = 0

    while True:
        try:
            now = time.time()
            dt = min(now - last, 0.1)
            last = now

            # 1) 追蹤子彈轉向
            for b in bullets:
                if not b.get("homing"):
                    continue
                best = None
                best_d2 = HOMING_RANGE * HOMING_RANGE
                for cid, p in players.items():
                    if cid == b["owner"] or not p["alive"]:
                        continue
                    dx = p["x"] - b["x"]; dy = p["y"] - b["y"]
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
                        cross = cx * ty - cy * tx
                        turn = HOMING_TURN_RATE * dt
                        turn = -turn if cross < 0 else turn
                        c, s = math.cos(turn), math.sin(turn)
                        b["vx"] = (cx * c - cy * s) * speed
                        b["vy"] = (cx * s + cy * c) * speed

            # 2) 子彈移動 + 命中
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
                    dx = p["x"] - b["x"]; dy = p["y"] - b["y"]
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

            # 3) 軌道護盾
            orbit_snapshot = []
            for cid, p in players.items():
                if not p["alive"] or now >= p["buffs"].get("orbit", 0):
                    continue
                for i in range(ORBIT_COUNT):
                    ang = now * ORBIT_ANGULAR_SPEED + i * 2 * math.pi / ORBIT_COUNT
                    ox = p["x"] + math.cos(ang) * ORBIT_RADIUS
                    oy = p["y"] + math.sin(ang) * ORBIT_RADIUS
                    orbit_snapshot.append({"owner_id": p["id"], "color": p["color"], "x": ox, "y": oy})
                    for vcid, vp in players.items():
                        if vcid == cid or not vp["alive"]:
                            continue
                        dx = vp["x"] - ox; dy = vp["y"] - oy
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

            # 3.5) 金手指 auto-regen
            for p in players.values():
                if not p["alive"] or not p.get("super"):
                    continue
                if now - p.get("last_regen", 0) > SUPER_REGEN_INTERVAL:
                    p["hp"] = min(eff_max_hp(p), p["hp"] + SUPER_REGEN)
                    p["last_regen"] = now

            # 4) 道具生成
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

            # 5) 撿道具
            for p in players.values():
                if not p["alive"]:
                    continue
                for pk in list(pickups):
                    dx = p["x"] - pk["x"]; dy = p["y"] - pk["y"]
                    hitr = 玩家半徑(p) + PICKUP_RADIUS
                    if dx * dx + dy * dy < hitr * hitr:
                        套用道具(p, pk["type"], now)
                        pickups.remove(pk)

            # 6) 廣播
            state = {
                "type":      "state",
                "players":   [打包玩家(p, now) for p in players.values()],
                "bullets":   [{"x": b["x"], "y": b["y"], "homing": b.get("homing", False),
                               "rainbow": b.get("rainbow", False), "tier": b.get("tier", 0)}
                              for b in bullets],
                "orbits":    orbit_snapshot,
                "pickups":   [{"x": pk["x"], "y": pk["y"], "type": pk["type"]} for pk in pickups],
                "chat_log":  list(chat_log),
                "kill_feed": list(kill_feed),
                "now":       now,
            }
            payload = json.dumps(state, ensure_ascii=False)
            await asyncio.gather(
                *[ws.send_str(payload) for ws in list(ws_of_cid.values()) if not ws.closed],
                return_exceptions=True,
            )
        except Exception as e:
            print("tick error:", e)

        await asyncio.sleep(1 / TICK_HZ)


# ====== HTTP handlers ======
async def index_handler(request):
    return web.FileResponse(STATIC_DIR / "index.html")


async def on_startup(app):
    app["tick"] = asyncio.create_task(遊戲Tick())


async def on_cleanup(app):
    app["tick"].cancel()


def main():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/ws", ws_handler)
    app.router.add_static("/static", str(STATIC_DIR))
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    print(f"Web server 開啟於 http://0.0.0.0:{PORT}/  (Ctrl+C 停止)")
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
