import asyncpg
import asyncio

async def create_db():
    # 連接到預設 postgres 資料庫
    conn = await asyncpg.connect(host='localhost', port=5432, user='postgres', password='961919', database='postgres')
    
    # 檢查資料庫是否存在
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'casetify_db'")
    
    if not exists:
        print('[建立資料庫中...]')
        await conn.execute('CREATE DATABASE casetify_db')
        print('[✅] 資料庫 casetify_db 已建立')
    else:
        print('[ℹ️] 資料庫 casetify_db 已存在')
    
    await conn.close()

asyncio.run(create_db())
