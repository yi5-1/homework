import sqlite3
from pathlib import Path
from aiohttp import web

BASE = Path(__file__).parent
DB_PATH = BASE / "app.db"

def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def 初始化資料庫():
    with db_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT UNIQUE NOT NULL,
                password   TEXT NOT NULL,
                role       TEXT NOT NULL DEFAULT 'buyer' CHECK (role IN ('buyer','seller')),
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                price       REAL NOT NULL CHECK (price >= 0),
                description TEXT DEFAULT '',
                image_url   TEXT DEFAULT '',
                seller_id   INTEGER NOT NULL REFERENCES users(id),
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS cart_items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity   INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
                created_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE (user_id, product_id)
            );
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                text       TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );
        """)
    print("[OK] 資料表已就緒 (SQLite)")

# ====== 靜態檔案 ======
async def 首頁(request):
    return web.FileResponse(BASE / "static" / "index.html")

# ====== 會員 API ======
async def api_註冊(request):
    data = await request.json()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    role = str(data.get("role", "buyer")).strip()

    if not username or not password:
        return web.json_response({"ok": False, "error": "帳號和密碼不能空白"}, status=400)
    if role not in ("buyer", "seller"):
        return web.json_response({"ok": False, "error": "角色必須是 buyer 或 seller"}, status=400)
    if len(username) > 20 or len(password) > 50:
        return web.json_response({"ok": False, "error": "帳號≤20字、密碼≤50字"}, status=400)

    with db_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role),
            )
        except sqlite3.IntegrityError:
            return web.json_response({"ok": False, "error": "此帳號已被註冊"}, status=400)

    return web.json_response({"ok": True, "message": f"註冊成功，歡迎 {username}（{role}）"})

async def api_登入(request):
    data = await request.json()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return web.json_response({"ok": False, "error": "請輸入帳號和密碼"}, status=400)

    with db_conn() as conn:
        row = conn.execute(
            "SELECT id, username, role FROM users WHERE username=? AND password=?",
            (username, password),
        ).fetchone()

    if row:
        return web.json_response({
            "ok": True,
            "message": f"登入成功，歡迎回來 {row['username']}",
            "user": {"id": row["id"], "username": row["username"], "role": row["role"]},
        })
    return web.json_response({"ok": False, "error": "帳號或密碼錯誤"}, status=401)

# ====== 商品 API ======
async def api_商品列表(request):
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT p.id, p.name, p.price, p.description, p.image_url,
                   p.seller_id, u.username AS seller_name
            FROM products p JOIN users u ON u.id = p.seller_id
            ORDER BY p.id
        """).fetchall()

    products = [{
        "id": r["id"], "name": r["name"], "price": r["price"],
        "description": r["description"], "image_url": r["image_url"],
        "seller_id": r["seller_id"], "seller_name": r["seller_name"],
    } for r in rows]

    return web.json_response({"ok": True, "products": products})

async def api_商家上架商品(request):
    data = await request.json()
    seller_id = int(data.get("seller_id", 0))
    name = str(data.get("name", "")).strip()
    price = float(data.get("price", 0))
    description = str(data.get("description", "")).strip()

    if seller_id < 1 or not name or price < 0:
        return web.json_response({"ok": False, "error": "名稱不能空白，價格不可為負"}, status=400)

    with db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO products (name, price, description, seller_id) VALUES (?, ?, ?, ?)",
            (name, price, description, seller_id),
        )
        product_id = cur.lastrowid

    return web.json_response({"ok": True, "message": "商品上架成功", "product_id": product_id})

async def api_商家儀表板(request):
    seller_id = int(request.query.get("seller_id", 0))
    if seller_id < 1:
        return web.json_response({"ok": False, "error": "缺少 seller_id"}, status=400)

    with db_conn() as conn:
        product_count = conn.execute(
            "SELECT COUNT(*) FROM products WHERE seller_id=?", (seller_id,)
        ).fetchone()[0]

        revenue = conn.execute("""
            SELECT COALESCE(SUM(p.price * c.quantity), 0)
            FROM cart_items c JOIN products p ON p.id = c.product_id
            WHERE p.seller_id = ?
        """, (seller_id,)).fetchone()[0]

        rows = conn.execute("""
            SELECT id, name, price, description, image_url, created_at
            FROM products WHERE seller_id=? ORDER BY id DESC
        """, (seller_id,)).fetchall()

    products = [{
        "id": r["id"], "name": r["name"], "price": r["price"],
        "description": r["description"], "image_url": r["image_url"],
        "created_at": r["created_at"],
    } for r in rows]

    return web.json_response({
        "ok": True,
        "product_count": product_count,
        "total_revenue": float(revenue),
        "products": products,
    })

async def api_加入購物車(request):
    data = await request.json()
    user_id = int(data.get("user_id", 0))
    product_id = int(data.get("product_id", 0))
    quantity = int(data.get("quantity", 1))

    if user_id < 1 or product_id < 1 or quantity < 1:
        return web.json_response({"ok": False, "error": "參數錯誤"}, status=400)

    with db_conn() as conn:
        try:
            conn.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, product_id)
                DO UPDATE SET quantity = quantity + ?
            """, (user_id, product_id, quantity, quantity))
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)}, status=400)

    return web.json_response({"ok": True, "message": "已加入購物車"})

async def api_更新購物車數量(request):
    data = await request.json()
    user_id = int(data.get("user_id", 0))
    product_id = int(data.get("product_id", 0))
    quantity = int(data.get("quantity", 0))

    if user_id < 1 or product_id < 1:
        return web.json_response({"ok": False, "error": "參數錯誤"}, status=400)

    with db_conn() as conn:
        if quantity < 1:
            conn.execute(
                "DELETE FROM cart_items WHERE user_id=? AND product_id=?",
                (user_id, product_id),
            )
            return web.json_response({"ok": True, "message": "已移除商品"})
        else:
            conn.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, product_id)
                DO UPDATE SET quantity = ?
            """, (user_id, product_id, quantity, quantity))
            return web.json_response({"ok": True, "message": "數量已更新"})

async def api_檢視購物車(request):
    user_id = int(request.query.get("user_id", 0))
    if user_id < 1:
        return web.json_response({"ok": False, "error": "缺少 user_id"}, status=400)

    with db_conn() as conn:
        rows = conn.execute("""
            SELECT c.id, c.product_id, c.quantity,
                   p.name, p.price, p.image_url
            FROM cart_items c JOIN products p ON p.id = c.product_id
            WHERE c.user_id=? ORDER BY c.id
        """, (user_id,)).fetchall()

    items = []
    total = 0
    for r in rows:
        subtotal = r["price"] * r["quantity"]
        total += subtotal
        items.append({
            "id": r["id"], "product_id": r["product_id"],
            "name": r["name"], "price": r["price"],
            "image_url": r["image_url"], "quantity": r["quantity"],
            "subtotal": round(subtotal, 2),
        })

    return web.json_response({"ok": True, "items": items, "total": round(total, 2)})

# ====== 留言板 API ======
async def api_取得訊息(request):
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT name, text, created_at FROM messages ORDER BY id DESC LIMIT 30"
        ).fetchall()
    return web.json_response([
        {"name": r["name"], "text": r["text"], "created_at": r["created_at"]} for r in rows
    ])

async def api_新增訊息(request):
    data = await request.json()
    name = str(data.get("name", "")).strip()[:20] or "匿名"
    text = str(data.get("text", "")).strip()[:200]
    if not text:
        return web.json_response({"error": "訊息不可空白"}, status=400)
    with db_conn() as conn:
        conn.execute("INSERT INTO messages (name, text) VALUES (?, ?)", (name, text))
    return web.json_response({"ok": True})

# ====== 啟動 ======
def main():
    初始化資料庫()

    app = web.Application()

    # 頁面
    app.router.add_get("/", 首頁)
    app.router.add_static("/static", path=BASE / "static", name="static")

    # 會員
    app.router.add_post("/api/register", api_註冊)
    app.router.add_post("/api/login", api_登入)

    # 商品
    app.router.add_get("/api/products", api_商品列表)
    app.router.add_post("/api/seller/products", api_商家上架商品)
    app.router.add_get("/api/seller/dashboard", api_商家儀表板)

    # 購物車
    app.router.add_post("/api/cart/add", api_加入購物車)
    app.router.add_post("/api/cart/update", api_更新購物車數量)
    app.router.add_get("/api/cart", api_檢視購物車)

    # 留言板
    app.router.add_get("/api/messages", api_取得訊息)
    app.router.add_post("/api/messages", api_新增訊息)

    port = 8000
    print("=" * 40)
    print("  DAY6 整合應用 — 啟動中")
    print("=" * 40)
    print(f"  SQLite:  {DB_PATH}")
    print(f"  Server:  http://127.0.0.1:{port}/\n")
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
