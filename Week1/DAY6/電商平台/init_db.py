"""執行此腳本建立資料表，並插入測試種子資料。"""

from models import init_db, get_db
from werkzeug.security import generate_password_hash

init_db()

conn = get_db()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)",
                ("admin", "admin@shop.local", generate_password_hash("admin123"), True),
            )
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                ("testuser", "user@shop.local", generate_password_hash("123456")),
            )

        cur.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] == 0:
            products = [
                ("無線藍牙耳機", "高音質 ANC 主動降噪", 1299, 50, True),
                ("機械式鍵盤", "青軸 RGB 背光", 2499, 30, True),
                ("27 吋 4K 螢幕", "IPS 面板 Type-C 供電", 12999, 15, True),
                ("電競滑鼠", "輕量化 65g 無線", 1890, 40, False),
                ("筆電支架", "鋁合金可調式", 890, 100, False),
            ]
            for p in products:
                cur.execute(
                    "INSERT INTO products (name, description, price, stock, is_hot) VALUES (%s, %s, %s, %s, %s)",
                    p,
            )
    conn.commit()
finally:
    conn.close()

print("資料表與種子資料已建立.")
