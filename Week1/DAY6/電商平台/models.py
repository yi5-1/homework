import psycopg2
from config import Config


def get_db():
    return psycopg2.connect(Config.dsn())


def init_db():
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id          SERIAL PRIMARY KEY,
        username    VARCHAR(50)  UNIQUE NOT NULL,
        email       VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_admin    BOOLEAN DEFAULT FALSE,
        created_at  TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS products (
        id          SERIAL PRIMARY KEY,
        name        VARCHAR(200) NOT NULL,
        description TEXT,
        price       NUMERIC(10,2) NOT NULL,
        stock       INTEGER DEFAULT 0,
        image_url   VARCHAR(500),
        is_hot      BOOLEAN DEFAULT FALSE,
        created_at  TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS cart_items (
        id          SERIAL PRIMARY KEY,
        user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
        product_id  INTEGER REFERENCES products(id) ON DELETE CASCADE,
        quantity    INTEGER DEFAULT 1,
        created_at  TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS orders (
        id          SERIAL PRIMARY KEY,
        user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
        total_amount NUMERIC(12,2) NOT NULL,
        status      VARCHAR(20) DEFAULT 'pending',
        created_at  TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id          SERIAL PRIMARY KEY,
        order_id    INTEGER REFERENCES orders(id) ON DELETE CASCADE,
        product_id  INTEGER REFERENCES products(id) ON DELETE CASCADE,
        quantity    INTEGER NOT NULL,
        price       NUMERIC(10,2) NOT NULL
    );
    """

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    finally:
        conn.close()
