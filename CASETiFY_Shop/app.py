"""
CASETiFY 式手機殼電商 - 第一階段後端
使用 aiohttp 框架，支援訪客購物車（localStorage）
"""

import os
import sys
from pathlib import Path
from aiohttp import web
import asyncpg
import json

# ===== 全局變量 =====
pool = None
BASE = Path(__file__).parent
db_config = {}

# ===== 資料庫連線配置 =====
def get_db_config():
    """
    讓使用者輸入 PostgreSQL 連線資訊
    """
    print("\n" + "="*60)
    print(" 🔐 PostgreSQL 資料庫連線設定")
    print("="*60)
    
    host = input("📍 Host (預設: localhost): ").strip() or "localhost"
    port = input("🔌 Port (預設: 5432): ").strip() or "5432"
    database = input("💾 Database 名稱: ").strip()
    user = input("👤 使用者名稱 (預設: postgres): ").strip() or "postgres"
    password = input("🔑 密碼: ").strip()
    
    if not database:
        print("❌ 錯誤：Database 名稱不能為空！")
        sys.exit(1)
    
    try:
        port = int(port)
    except ValueError:
        print("❌ 錯誤：Port 必須是數字！")
        sys.exit(1)
    
    return {
        'host': host,
        'port': port,
        'database': database,
        'user': user,
        'password': password,
    }

# ===== API 路由 =====
async def handle_index(request):
    """首頁"""
    return web.FileResponse(BASE / "static" / "index.html")

async def api_products(request):
    """
    GET /api/products
    獲取所有商品列表（按分類分組）
    """
    try:
        async with pool.acquire() as conn:
            # 獲取所有分類
            categories = await conn.fetch("""
                SELECT id, name, display_name, icon 
                FROM categories 
                ORDER BY id
            """)
            
            result = {}
            for cat in categories:
                products = await conn.fetch("""
                    SELECT 
                        id, name, price, color, description, 
                        image_url, stock, category_id
                    FROM products 
                    WHERE category_id = $1 
                    ORDER BY id
                """, cat['id'])
                
                result[cat['name']] = {
                    'display_name': cat['display_name'],
                    'icon': cat['icon'],
                    'products': [
                        {
                            'id': p['id'],
                            'name': p['name'],
                            'price': float(p['price']),
                            'color': p['color'],
                            'description': p['description'],
                            'image_url': p['image_url'],
                            'stock': p['stock'],
                        }
                        for p in products
                    ]
                }
        
        return web.json_response({
            'ok': True,
            'data': result
        })
    
    except Exception as e:
        return web.json_response({
            'ok': False,
            'error': str(e)
        }, status=500)

# ===== 資料庫初始化 =====
async def init_db(conn):
    """執行 schema.sql 初始化資料庫"""
    schema_file = BASE / "schema.sql"
    if schema_file.exists():
        schema_sql = schema_file.read_text(encoding='utf-8')
        await conn.execute(schema_sql)
        print("[✅] 資料庫初始化完成")
    else:
        print("[⚠️] schema.sql 檔案未找到")

async def on_startup(app):
    """應用啟動時建立資料庫連線池"""
    global pool
    try:
        print("\n[⏳] 連接 PostgreSQL...")
        pool = await asyncpg.create_pool(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            min_size=2,
            max_size=10
        )
        print(f"[✅] 成功連接 {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # 初始化資料庫結構
        async with pool.acquire() as conn:
            await init_db(conn)
    
    except Exception as e:
        print(f"[❌] 連接失敗：{e}")
        sys.exit(1)

async def on_cleanup(app):
    """應用結束時關閉連線池"""
    global pool
    if pool:
        await pool.close()

def main():
    """啟動應用"""
    global db_config
    
    print("\n" + "="*60)
    print(" 🛍️  脫殼 手機殼電商 - 第一階段")
    print("="*60)
    
    # 獲取資料庫配置
    db_config = get_db_config()
    
    # 建立應用
    app = web.Application()
    
    # 路由
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/products', api_products)
    app.router.add_static('/static', path=BASE / 'static', name='static')
    
    # 生命週期
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    # 啟動伺服器
    port = 8000
    print(f"\n[🚀] 伺服器啟動於 http://localhost:{port}/")
    print(f"[💡] 按 Ctrl+C 停止伺服器\n")
    
    web.run_app(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
