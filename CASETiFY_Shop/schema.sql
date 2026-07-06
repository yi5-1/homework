-- ============================================================
-- CASETiFY 式手機殼電商 - 第一階段資料庫架構
-- ============================================================

-- 分類表
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    icon CHAR(2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 商品表
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    color VARCHAR(100),
    description TEXT DEFAULT '',
    image_url VARCHAR(500),
    stock INTEGER DEFAULT 100 CHECK (stock >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);

-- 插入默認分類
INSERT INTO categories (name, display_name, icon) VALUES 
    ('floral', '花卉系列', '🌸'),
    ('animal', '動物系列', '🐾'),
    ('food', '食物系列', '🍕'),
    ('ballet', '芭蕾風格', '🩰'),
    ('abstract', '抽象藝術', '🎨'),
    ('dnd', 'DND 冒險', '🐉')
ON CONFLICT (name) DO NOTHING;

-- 插入示例商品
INSERT INTO products (name, category_id, price, color, description, image_url) VALUES 
    -- 花卉系列
    ('波紋手機殼', 1, 1299, '蕃茄紅', '優雅的波紋設計，展現自然之美', '/static/images/wave-tomato.jpg'),
    ('花卉印花殼', 1, 1399, '粉紅色', '精美的花卉圖案印刷', '/static/images/floral-pink.jpg'),
    ('玫瑰金框殼', 1, 1599, '金色', '奢華感玫瑰金邊框', '/static/images/rose-gold.jpg'),
    
    -- 動物系列
    ('小貓咪殼', 2, 1299, '白色', '可愛的貓咪圖案', '/static/images/cat-white.jpg'),
    ('小狗汪汪殼', 2, 1299, '棕色', '活潑的狗狗表情', '/static/images/dog-brown.jpg'),
    ('企鵝朋友殼', 2, 1199, '黑白色', '呆萌的企鵝設計', '/static/images/penguin.jpg'),
    
    -- 食物系列
    ('草莓甜蜜殼', 3, 1299, '紅色', '新鮮的草莓圖案', '/static/images/strawberry-red.jpg'),
    ('檸檬清爽殼', 3, 1299, '黃色', '清新的檸檬元素', '/static/images/lemon-yellow.jpg'),
    ('披薩派對殼', 3, 1499, '橙色', '趣味十足的披薩設計', '/static/images/pizza-orange.jpg'),
    
    -- 芭蕾風格
    ('芭蕾舞者殼', 4, 1899, '紫紅色', '優雅的芭蕾舞者剪影', '/static/images/ballet-purple.jpg'),
    ('芭蕾粉色夢', 4, 1799, '粉色', '柔和的粉色芭蕾主題', '/static/images/ballet-pink.jpg'),
    
    -- 抽象藝術
    ('幾何拼圖殼', 5, 1499, '藍莓紫', '現代幾何圖形設計', '/static/images/geometry-purple.jpg'),
    ('漸變彩虹殼', 5, 1399, '彩色', '漸變色彩效果', '/static/images/gradient-rainbow.jpg'),
    
    -- DND 冒險系列
    ('龍族守護殼', 6, 1699, '黑金色', '威猛的龍族圖案，保護您的手機', '/static/images/dnd-dragon.jpg'),
    ('法師魔法殼', 6, 1599, '紫藍色', '神祕的法師魔法陣設計', '/static/images/dnd-mage.jpg'),
    ('騎士盔甲殼', 6, 1799, '銀白色', '堅固的騎士盔甲風格', '/static/images/dnd-knight.jpg'),
    ('冒險家探險殼', 6, 1499, '棕色', '冒險家的地圖與羅盤圖案', '/static/images/dnd-adventure.jpg'),
    ('寶藏獵人殼', 6, 1599, '金黃色', '尋寶的刺激感', '/static/images/dnd-treasure.jpg'),
    ('暗夜精靈殼', 6, 1599, '深綠色', '優雅的暗夜精靈文明風格', '/static/images/dnd-elf.jpg')
ON CONFLICT DO NOTHING;
