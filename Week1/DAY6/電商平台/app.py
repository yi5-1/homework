from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from models import get_db, init_db

app = Flask(__name__)
app.config.from_object("config.Config")

init_db()


def login_required(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"ok": False, "message": "請先登入"}), 401
        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return jsonify({"ok": False, "message": "需要管理員權限"}), 403
        return f(*args, **kwargs)

    return wrapper


# ─── 頁面路由 ──────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/products")
def products_page():
    return render_template("products.html")


@app.route("/cart")
def cart_page():
    return render_template("cart.html")


@app.route("/checkout")
def checkout_page():
    return render_template("checkout.html")


@app.route("/admin/login")
def admin_login_page():
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard_page():
    return render_template("admin_dashboard.html")


# ─── 使用者認證 API ────────────────────────────


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"ok": False, "message": "請填寫所有欄位"}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE username=%s OR email=%s",
                (username, email),
            )
            if cur.fetchone():
                return jsonify({"ok": False, "message": "帳號或信箱已存在"}), 400

            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (username, email, generate_password_hash(password)),
            )
            user_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    session["user_id"] = user_id
    session["username"] = username
    return jsonify({"ok": True, "message": "註冊成功", "user": {"id": user_id, "username": username, "email": email}}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password_hash FROM users WHERE username=%s",
                (username,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row or not check_password_hash(row[2], password):
        return jsonify({"ok": False, "message": "帳號或密碼錯誤"}), 401

    session["user_id"] = row[0]
    session["username"] = row[1]
    return jsonify({"ok": True, "message": "登入成功", "user": {"id": row[0], "username": row[1]}})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True, "message": "已登出"})


@app.route("/api/me")
def me():
    if "user_id" not in session:
        return jsonify({"ok": False, "message": "未登入"}), 401
    return jsonify({"ok": True, "user": {"id": session["user_id"], "username": session["username"], "is_admin": session.get("is_admin", False)}})


# ─── 商品 API ──────────────────────────────────


@app.route("/api/products")
def list_products():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description, price, stock, image_url, is_hot FROM products ORDER BY id")
            rows = cur.fetchall()
    finally:
        conn.close()

    products = [
        {
            "id": r[0],
            "name": r[1],
            "description": r[2],
            "price": float(r[3]),
            "stock": r[4],
            "image_url": r[5],
            "is_hot": r[6],
        }
        for r in rows
    ]
    return jsonify({"ok": True, "products": products})


@app.route("/api/products/hot")
def hot_products():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description, price, stock, image_url FROM products WHERE is_hot=TRUE ORDER BY id"
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    products = [
        {
            "id": r[0],
            "name": r[1],
            "description": r[2],
            "price": float(r[3]),
            "stock": r[4],
            "image_url": r[5],
        }
        for r in rows
    ]
    return jsonify({"ok": True, "products": products})


@app.route("/api/products/<int:product_id>")
def get_product(product_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description, price, stock, image_url FROM products WHERE id=%s",
                (product_id,),
            )
            r = cur.fetchone()
    finally:
        conn.close()

    if not r:
        return jsonify({"ok": False, "message": "商品不存在"}), 404

    return jsonify(
        {
            "ok": True,
            "product": {
                "id": r[0],
                "name": r[1],
                "description": r[2],
                "price": float(r[3]),
                "stock": r[4],
                "image_url": r[5],
            },
        }
    )


# ─── 購物車 API ────────────────────────────────


@app.route("/api/cart", methods=["GET"])
@login_required
def get_cart():
    user_id = session["user_id"]
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT ci.id, ci.product_id, p.name, p.price, ci.quantity
                   FROM cart_items ci
                   JOIN products p ON p.id = ci.product_id
                   WHERE ci.user_id=%s""",
                (user_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    items = []
    total = 0.0
    for r in rows:
        subtotal = float(r[3]) * r[4]
        items.append(
            {
                "id": r[0],
                "product_id": r[1],
                "product_name": r[2],
                "price": float(r[3]),
                "quantity": r[4],
                "subtotal": subtotal,
            }
        )
        total += subtotal

    return jsonify({"ok": True, "items": items, "total": total})


@app.route("/api/cart", methods=["POST"])
@login_required
def add_to_cart():
    data = request.get_json()
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    user_id = session["user_id"]

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, quantity FROM cart_items WHERE user_id=%s AND product_id=%s",
                (user_id, product_id),
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE cart_items SET quantity=quantity+%s WHERE id=%s",
                    (quantity, existing[0]),
                )
            else:
                cur.execute(
                    "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                    (user_id, product_id, quantity),
                )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"ok": True, "message": "已加入購物車"})


@app.route("/api/cart/<int:item_id>", methods=["PUT"])
@login_required
def update_cart(item_id):
    data = request.get_json()
    quantity = data.get("quantity", 1)
    user_id = session["user_id"]

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE cart_items SET quantity=%s WHERE id=%s AND user_id=%s",
                (quantity, item_id, user_id),
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"ok": True, "message": "數量已更新"})


@app.route("/api/cart/<int:item_id>", methods=["DELETE"])
@login_required
def remove_from_cart(item_id):
    user_id = session["user_id"]

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM cart_items WHERE id=%s AND user_id=%s",
                (item_id, user_id),
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"ok": True, "message": "已移除"})


# ─── 結帳 API ──────────────────────────────────


@app.route("/api/checkout", methods=["POST"])
@login_required
def checkout():
    user_id = session["user_id"]

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT ci.product_id, ci.quantity, p.price
                   FROM cart_items ci
                   JOIN products p ON p.id = ci.product_id
                   WHERE ci.user_id=%s""",
                (user_id,),
            )
            items = cur.fetchall()

            if not items:
                return jsonify({"ok": False, "message": "購物車為空"}), 400

            total = sum(float(r[2]) * r[1] for r in items)
            cur.execute(
                "INSERT INTO orders (user_id, total_amount) VALUES (%s, %s) RETURNING id",
                (user_id, total),
            )
            order_id = cur.fetchone()[0]

            for r in items:
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                    (order_id, r[0], r[1], r[2]),
                )

            cur.execute("DELETE FROM cart_items WHERE user_id=%s", (user_id,))
        conn.commit()
    finally:
        conn.close()

    return jsonify({"ok": True, "message": "訂單成立", "order_id": order_id, "total_amount": float(total)})


# ─── 後台管理 API ──────────────────────────────


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password_hash, is_admin FROM users WHERE username=%s",
                (username,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row or not check_password_hash(row[2], password) or not row[3]:
        return jsonify({"ok": False, "message": "權限不足或密碼錯誤"}), 401

    session["user_id"] = row[0]
    session["username"] = row[1]
    session["is_admin"] = True
    return jsonify({"ok": True, "message": "管理員登入成功"})


@app.route("/api/admin/stats")
@admin_required
def admin_stats():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]

            cur.execute(
                """SELECT u.id, u.username, COALESCE(SUM(o.total_amount), 0) AS total_spent
                   FROM users u
                   LEFT JOIN orders o ON o.user_id = u.id
                   GROUP BY u.id, u.username
                   ORDER BY total_spent DESC"""
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    user_spending = [
        {"user_id": r[0], "username": r[1], "total_spent": float(r[2])} for r in rows
    ]

    return jsonify({"ok": True, "total_users": total_users, "user_spending": user_spending})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8097, debug=True)
