from flask import Flask

app = Flask(__name__)

# 共用的 CSS 樣式，這樣兩個頁面風格才會統一
SHARED_STYLE = """
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Helvetica Neue', Arial, sans-serif; }
    body { background-color: #f9f9f9; color: #333; line-height: 1.6; }
    header { background-color: #ffffff; padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); position: sticky; top: 0; z-index: 100; }
    .logo { font-size: 24px; font-weight: bold; letter-spacing: 2px; text-decoration: none; color: #222; }
    nav a { text-decoration: none; color: #555; margin-left: 20px; font-size: 14px; transition: color 0.3s; }
    nav a:hover { color: #000; }
    .container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
    .product-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; margin-top: 20px; }
    .product-card { background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.03); transition: transform 0.3s; }
    .product-card:hover { transform: translateY(-5px); }
    .product-img { width: 100%; height: 250px; display: flex; justify-content: center; align-items: center; color: #888; font-size: 14px; }
    .product-info { padding: 20px; }
    .product-name { font-size: 18px; margin-bottom: 10px; }
    .product-price { color: #e44d26; font-weight: bold; font-size: 16px; margin-bottom: 15px; }
    .buy-btn { width: 100%; background-color: #fff; border: 1px solid #222; color: #222; padding: 10px; font-size: 14px; cursor: pointer; border-radius: 4px; transition: all 0.3s; }
    .buy-btn:hover { background-color: #222; color: #fff; }
    footer { background-color: #222; color: #fff; text-align: center; padding: 40px 20px; font-size: 14px; margin-top: 60px; }
</style>
"""

# 共通的 導覽列 與 頁尾
HEADER_HTML = f"""
<header>
    <a href="/" class="logo">MINIMAL</a>
    <nav>
        <a href="/">首頁</a>
        <a href="/explore">立即探索</a>
    </nav>
</header>
"""
FOOTER_HTML = "<footer><p>&copy; 2026 MINIMAL Studio. All Rights Reserved.</p></footer>"


# --- 路由 1：首頁 ---
@app.route("/")
def home():
    return f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>極簡美學 | 質感生活選物</title>
        {SHARED_STYLE}
        <style>
            .hero {{ background: linear-gradient(135deg, #e0e0e0 0%, #f5f5f5 100%); height: 70vh; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 0 20px; }}
            .hero h1 {{ font-size: 42px; margin-bottom: 15px; letter-spacing: 1px; }}
            .hero p {{ font-size: 18px; color: #666; margin-bottom: 30px; }}
            .cta-btn {{ background-color: #222; color: #fff; padding: 12px 30px; text-decoration: none; font-size: 16px; border-radius: 4px; transition: background 0.3s; }}
            .cta-btn:hover {{ background-color: #444; }}
        </style>
    </head>
    <body>
        {HEADER_HTML}
        
        <section class="hero">
            <h1>用極簡，定義你的生活美學</h1>
            <p>嚴選天然材質與工匠手作，為日常帶來一份靜謐的質感。</p>
            <a href="/explore" class="cta-btn">立即探索系列商品</a>
        </section>

        {FOOTER_HTML}
    </body>
    </html>
    """


# --- 路由 2：立即探索頁面 ---
@app.route("/explore")
def explore():
    return f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>探索所有商品 | MINIMAL</title>
        {SHARED_STYLE}
    </head>
    <body>
        {HEADER_HTML}
        
        <div class="container">
            <h2 style="font-size: 28px; margin-bottom: 10px;">探索所有商品</h2>
            <p style="color: #777; margin-bottom: 30px;">在這裡尋找適合你空間的完美單品。</p>
            
            <div class="product-grid">
                <div class="product-card">
                    <div class="product-img" style="background-color: #eae6df;">【 陶瓷系列 】</div>
                    <div class="product-info">
                        <h3 class="product-name">手工陶瓷馬克杯</h3>
                        <p class="product-price">NT$ 680</p>
                        <button class="buy-btn" onclick="alert('已加入購物車')">加入購物車</button>
                    </div>
                </div>
                <div class="product-card">
                    <div class="product-img" style="background-color: #e2e8f0;">【 香氛系列 】</div>
                    <div class="product-info">
                        <h3 class="product-name">天然大豆香氛蠟燭</h3>
                        <p class="product-price">NT$ 850</p>
                        <button class="buy-btn" onclick="alert('已加入購物車')">加入購物車</button>
                    </div>
                </div>
                <div class="product-card">
                    <div class="product-img" style="background-color: #e2eee2;">【 織品系列 】</div>
                    <div class="product-info">
                        <h3 class="product-name">極簡亞麻抱枕套</h3>
                        <p class="product-price">NT$ 520</p>
                        <button class="buy-btn" onclick="alert('已加入購物車')">加入購物車</button>
                    </div>
                </div>
                <div class="product-card">
                    <div class="product-img" style="background-color: #f4e3e3;">【 燈具系列 】</div>
                    <div class="product-info">
                        <h3 class="product-name">日系復古桌燈</h3>
                        <p class="product-price">NT$ 1,880</p>
                        <button class="buy-btn" onclick="alert('已加入購物車')">加入購物車</button>
                    </div>
                </div>
            </div>
        </div>

        {FOOTER_HTML}
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)