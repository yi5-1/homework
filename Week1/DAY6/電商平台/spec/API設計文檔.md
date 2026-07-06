# 電商平台 — API 設計文檔

Base URL: `http://localhost:8097/api`

---

## 1. 使用者認證

### POST /api/register
註冊新使用者。

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response 201:**
```json
{
  "ok": true,
  "message": "註冊成功",
  "user": { "id": 1, "username": "string", "email": "string" }
}
```

**Response 400:**
```json
{ "ok": false, "message": "帳號或信箱已存在" }
```

---

### POST /api/login
一般使用者登入。

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200:**
```json
{
  "ok": true,
  "message": "登入成功",
  "user": { "id": 1, "username": "string" }
}
```

**Response 401:**
```json
{ "ok": false, "message": "帳號或密碼錯誤" }
```

---

### POST /api/logout
登出（清除 session）。

**Response 200:**
```json
{ "ok": true, "message": "已登出" }
```

---

## 2. 商品

### GET /api/products
取得所有商品列表。

**Response 200:**
```json
{
  "ok": true,
  "products": [
    {
      "id": 1,
      "name": "string",
      "description": "string",
      "price": 100.00,
      "stock": 10,
      "image_url": "string",
      "is_hot": false
    }
  ]
}
```

---

### GET /api/products/hot
取得熱門商品列表。

**Response 200:** （同上，僅回傳 is_hot = true 的商品）

---

### GET /api/products/<id>
取得單一商品詳細資訊。

**Response 200:**
```json
{
  "ok": true,
  "product": { "id": 1, "name": "string", "description": "string", "price": 100.00, "stock": 10, "image_url": "string" }
}
```

**Response 404:**
```json
{ "ok": false, "message": "商品不存在" }
```

---

## 3. 購物車

> 以下 API 需要 session（已登入狀態）。

### GET /api/cart
取得當前使用者的購物車內容。

**Response 200:**
```json
{
  "ok": true,
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "product_name": "string",
      "price": 100.00,
      "quantity": 2,
      "subtotal": 200.00
    }
  ],
  "total": 200.00
}
```

---

### POST /api/cart
加入商品到購物車。

**Request Body:**
```json
{
  "product_id": 1,
  "quantity": 1
}
```

**Response 200:**
```json
{ "ok": true, "message": "已加入購物車" }
```

---

### PUT /api/cart/<item_id>
更新購物車商品數量。

**Request Body:**
```json
{ "quantity": 3 }
```

**Response 200:**
```json
{ "ok": true, "message": "數量已更新" }
```

---

### DELETE /api/cart/<item_id>
移除購物車中的商品。

**Response 200:**
```json
{ "ok": true, "message": "已移除" }
```

---

## 4. 結帳

> 需要 session（已登入狀態）。

### POST /api/checkout
將購物車內容建立為訂單。

**Response 200:**
```json
{
  "ok": true,
  "message": "訂單成立",
  "order_id": 1,
  "total_amount": 500.00
}
```

**Response 400:**
```json
{ "ok": false, "message": "購物車為空" }
```

---

## 5. 後台管理

### POST /api/admin/login
管理員登入。

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200:**
```json
{ "ok": true, "message": "管理員登入成功" }
```

**Response 401:**
```json
{ "ok": false, "message": "權限不足或密碼錯誤" }
```

---

### GET /api/admin/stats
取得後台報表統計。

> 需要管理員 session。

**Response 200:**
```json
{
  "ok": true,
  "total_users": 10,
  "user_spending": [
    { "user_id": 1, "username": "string", "total_spent": 1500.00 },
    { "user_id": 2, "username": "string", "total_spent": 800.00 }
  ]
}
```

---

## 6. 頁面路由

| 方法 | 路由 | 說明 |
|------|------|------|
| GET | `/` | 首頁 |
| GET | `/products` | 商品列表頁 |
| GET | `/cart` | 購物車頁 |
| GET | `/checkout` | 結帳頁 |
| GET | `/admin/login` | 後台登入頁 |
| GET | `/admin/dashboard` | 後台儀表板 |
