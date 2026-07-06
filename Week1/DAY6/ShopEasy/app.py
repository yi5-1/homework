import os
from pathlib import Path

from dotenv import load_dotenv
from aiohttp import web
import asyncpg

load_dotenv()

BASE = Path(__file__).parent

DB_CONFIG: dict = {}
pool: asyncpg.Pool | None = None


async def 建立資料表():
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         SERIAL PRIMARY KEY,
                username   TEXT UNIQUE NOT NULL,
                password   TEXT NOT NULL,
                role       TEXT NOT NULL CHECK (role IN ('buyer', 'seller')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id          SERIAL PRIMARY KEY,
                name        TEXT NOT NULL,
                price       NUMERIC(10,2) NOT NULL CHECK (price >= 0),
                description TEXT DEFAULT '',
                image_url   TEXT DEFAULT '',
                seller_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id         SERIAL PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                quantity   INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, product_id)
            )
        """)
        print("[OK] users / products / cart_items 資料表已就緒")


async def 首頁(request):
    return web.FileResponse(BASE / "static" / "index.html")


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

    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO users (username, password, role) VALUES ($1, $2, $3)",
                username, password, role,
            )
        except asyncpg.UniqueViolationError:
            return web.json_response({"ok": False, "error": "此帳號已被註冊"}, status=400)

    return web.json_response({"ok": True, "message": f"註冊成功，歡迎 {username}（{role}）"})


async def api_登入(request):
    data = await request.json()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return web.json_response({"ok": False, "error": "請輸入帳號和密碼"}, status=400)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, role FROM users WHERE username=$1 AND password=$2",
            username, password,
        )

    if row:
        return web.json_response({
            "ok": True,
            "message": f"登入成功，歡迎回來 {row['username']}",
            "user": {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
            },
        })
    return web.json_response({"ok": False, "error": "帳號或密碼錯誤"}, status=401)


async def api_商品列表(request):
    所有商品 = []
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT p.id, p.name, p.price, p.description, p.image_url,
                   p.seller_id, u.username AS seller_name
            FROM products p
            JOIN users u ON u.id = p.seller_id
            ORDER BY p.id
        """)
        for r in rows:
            所有商品.append({
                "id": r["id"],
                "name": r["name"],
                "price": float(r["price"]),
                "description": r["description"],
                "image_url": r["image_url"],
                "seller_id": r["seller_id"],
                "seller_name": r["seller_name"],
            })
    return web.json_response({"ok": True, "products": 所有商品})


async def api_加入購物車(request):
    data = await request.json()
    user_id = int(data.get("user_id", 0))
    product_id = int(data.get("product_id", 0))
    quantity = int(data.get("quantity", 1))

    if user_id < 1 or product_id < 1 or quantity < 1:
        return web.json_response({"ok": False, "error": "參數錯誤"}, status=400)

    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + $3
            """, user_id, product_id, quantity)
            row = await conn.fetchrow(
                "SELECT id, product_id, quantity FROM cart_items WHERE user_id=$1 AND product_id=$2",
                user_id, product_id,
            )
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)}, status=400)

    return web.json_response({
        "ok": True,
        "message": "已加入購物車",
        "item": {"id": row["id"], "product_id": row["product_id"], "quantity": row["quantity"]},
    })


async def api_更新購物車數量(request):
    data = await request.json()
    user_id = int(data.get("user_id", 0))
    product_id = int(data.get("product_id", 0))
    quantity = int(data.get("quantity", 0))

    if user_id < 1 or product_id < 1:
        return web.json_response({"ok": False, "error": "參數錯誤"}, status=400)

    async with pool.acquire() as conn:
        if quantity < 1:
            await conn.execute(
                "DELETE FROM cart_items WHERE user_id=$1 AND product_id=$2",
                user_id, product_id,
            )
            return web.json_response({"ok": True, "message": "已移除商品"})
        else:
            await conn.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET quantity = $3
            """, user_id, product_id, quantity)
            return web.json_response({"ok": True, "message": "數量已更新"})


async def api_檢視購物車(request):
    user_id = int(request.query.get("user_id", 0))
    if user_id < 1:
        return web.json_response({"ok": False, "error": "缺少 user_id"}, status=400)

    項目列表 = []
    總金額 = 0
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.product_id, c.quantity,
                   p.name, p.price, p.image_url
            FROM cart_items c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = $1
            ORDER BY c.id
        """, user_id)
        for r in rows:
            小計 = float(r["price"]) * r["quantity"]
            總金額 += 小計
            項目列表.append({
                "id": r["id"],
                "product_id": r["product_id"],
                "name": r["name"],
                "price": float(r["price"]),
                "image_url": r["image_url"],
                "quantity": r["quantity"],
                "subtotal": round(小計, 2),
            })

    return web.json_response({
        "ok": True,
        "items": 項目列表,
        "total": round(總金額, 2),
    })


async def api_商家上架商品(request):
    data = await request.json()
    seller_id = int(data.get("seller_id", 0))
    name = str(data.get("name", "")).strip()
    price = float(data.get("price", 0))
    description = str(data.get("description", "")).strip()

    if seller_id < 1 or not name or price < 0:
        return web.json_response({"ok": False, "error": "名稱不能空白，價格不可為負"}, status=400)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO products (name, price, description, seller_id) VALUES ($1, $2, $3, $4) RETURNING id",
            name, price, description, seller_id,
        )

    return web.json_response({"ok": True, "message": "商品上架成功", "product_id": row["id"]})


async def api_商家儀表板(request):
    seller_id = int(request.query.get("seller_id", 0))
    if seller_id < 1:
        return web.json_response({"ok": False, "error": "缺少 seller_id"}, status=400)

    async with pool.acquire() as conn:
        product_count_row = await conn.fetchval(
            "SELECT COUNT(*) FROM products WHERE seller_id=$1", seller_id,
        )
        revenue_row = await conn.fetchval("""
            SELECT COALESCE(SUM(p.price * c.quantity), 0)
            FROM cart_items c
            JOIN products p ON p.id = c.product_id
            WHERE p.seller_id = $1
        """, seller_id)
        products_rows = await conn.fetch("""
            SELECT id, name, price, description, image_url, created_at
            FROM products WHERE seller_id = $1 ORDER BY id DESC
        """, seller_id)

    products = [
        {
            "id": r["id"],
            "name": r["name"],
            "price": float(r["price"]),
            "description": r["description"],
            "image_url": r["image_url"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else "",
        }
        for r in products_rows
    ]

    return web.json_response({
        "ok": True,
        "product_count": product_count_row,
        "total_revenue": float(revenue_row),
        "products": products,
    })


async def on_startup(app):
    global pool
    try:
        pool = await asyncpg.create_pool(**DB_CONFIG, min_size=1, max_size=5)
    except Exception as e:
        print(f"[錯誤] 連不上 PostgreSQL：{e}")
        print(f"       設定：{DB_CONFIG}")
        raise
    await 建立資料表()
    print(f"[OK] 已連上 PostgreSQL {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")


async def on_cleanup(app):
    if pool:
        await pool.close()


def main():
    print("=" * 50)
    print("  ShopEasy — 啟動中")
    print("=" * 50)

    DB_CONFIG["host"] = os.getenv("DB_HOST", "localhost")
    DB_CONFIG["port"] = int(os.getenv("DB_PORT", "5432"))
    DB_CONFIG["database"] = os.getenv("DB_NAME", "ecommerce")
    DB_CONFIG["user"] = os.getenv("DB_USER", "postgres")
    DB_CONFIG["password"] = os.getenv("DB_PASSWORD", "")

    print(f"  PostgreSQL  {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"  Server 埠   {os.getenv('SERVER_PORT', '8001')}\n")
    print("[OK] 設定完成，啟動伺服器...\n")

    app = web.Application()
    app.router.add_get("/", 首頁)
    app.router.add_static("/static", path=BASE / "static", name="static")
    app.router.add_post("/api/register", api_註冊)
    app.router.add_post("/api/login", api_登入)
    app.router.add_get("/api/products", api_商品列表)
    app.router.add_post("/api/cart/add", api_加入購物車)
    app.router.add_post("/api/cart/update", api_更新購物車數量)
    app.router.add_get("/api/cart", api_檢視購物車)
    app.router.add_post("/api/seller/products", api_商家上架商品)
    app.router.add_get("/api/seller/dashboard", api_商家儀表板)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    port = int(os.getenv("SERVER_PORT", "8001"))
    print(f"Server 開啟於 http://127.0.0.1:{port}/  (Ctrl+C 停止)")
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
