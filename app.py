from flask import Flask

app = Flask(__name__, static_folder="web_basics/img", static_url_path="/img")


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Braun 電鬍刀產品頁</title>
    <style>
        :root {
            --bg: #f5f7fb;
            --card: #ffffff;
            --text: #111827;
            --muted: #6b7280;
            --accent: #0f766e;
            --accent2: #2563eb;
            --border: #e5e7eb;
        }

        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
            color: var(--text);
        }

        a { color: inherit; text-decoration: none; }
        .wrap { max-width: 1200px; margin: 0 auto; padding: 24px; }

        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 18px 0 28px;
        }

        .brand {
            font-size: 24px;
            font-weight: 900;
            letter-spacing: 2px;
        }

        nav a {
            margin-left: 20px;
            color: var(--muted);
            font-weight: 600;
        }

        .hero {
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 24px;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 32px;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
        }

        .hero h1 {
            font-size: 36px;
            line-height: 1.2;
            margin: 0 0 14px;
        }

        .hero p {
            color: var(--muted);
            font-size: 18px;
            line-height: 1.7;
            margin-bottom: 20px;
        }

        .btn {
            display: inline-block;
            padding: 12px 20px;
            border-radius: 999px;
            font-weight: 700;
            margin-right: 12px;
            margin-bottom: 8px;
        }

        .btn-primary { background: var(--accent); color: white; }
        .btn-secondary { background: #eef2ff; color: var(--accent2); }

        .hero-card {
            background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%);
            color: white;
            border-radius: 20px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 260px;
        }

        .hero-card img {
            width: 100%;
            height: 220px;
            object-fit: cover;
            border-radius: 16px;
            margin-bottom: 16px;
        }

        .hero-card .badge {
            display: inline-block;
            width: fit-content;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(255,255,255,0.16);
            font-size: 12px;
            margin-bottom: 12px;
        }

        .section {
            margin-top: 24px;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 24px;
        }

        .section h2 {
            margin-top: 0;
            margin-bottom: 16px;
            font-size: 24px;
        }

        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }

        .card {
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 18px;
            background: #fbfdff;
        }

        .card img {
            width: 100%;
            height: 160px;
            object-fit: cover;
            border-radius: 10px;
            margin-bottom: 10px;
        }

        .card h3 { margin: 8px 0; }
        .card p { color: var(--muted); line-height: 1.6; }

        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }

        .gallery-item {
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            background: #fbfdff;
        }

        .gallery-item img {
            width: 100%;
            height: 180px;
            object-fit: cover;
            display: block;
        }

        .gallery-item .caption {
            padding: 12px;
            color: var(--muted);
            font-size: 14px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        th, td {
            border-bottom: 1px solid var(--border);
            padding: 12px 8px;
            text-align: left;
        }

        th { color: var(--muted); }

        .faq-item {
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
        }

        footer {
            text-align: center;
            padding: 32px 0 24px;
            color: var(--muted);
        }

        @media (max-width: 900px) {
            .hero, .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="wrap">
        <header class="topbar">
            <div class="brand">BRAUN</div>
            <nav>
                <a href="#product">產品</a>
                <a href="#gallery">圖片展示</a>
                <a href="#support">支援</a>
            </nav>
        </header>

        <section class="hero">
            <div>
                <h1>高效、輕柔、貼合肌膚的電鬍刀新體驗</h1>
                <p>從 1 日到 7 日鬍渣，都能用更乾淨、更快速的方式完成剃鬍。</p>
                <a class="btn btn-primary" href="#product">探索產品</a>
                <a class="btn btn-secondary" href="#gallery">觀看圖片</a>
            </div>
            <div class="hero-card">
                <img src="/img/stage_series-9-pro-plus-desktop.avif" alt="Series 9 Pro Plus 主視覺">
                <div>
                    <span class="badge">新品推薦</span>
                    <h2>Series 9 Pro+</h2>
                    <p>智慧感應、強勁切割、舒適貼面，帶來更好的每日剃鬍體驗。</p>
                </div>
                <div>⏱ 60 分鐘續航 • 防水 • 快速充電</div>
            </div>
        </section>

        <section id="product" class="section">
            <h2>熱門產品</h2>
            <div class="grid">
                <article class="card">
                    <img src="/img/category-tile-shavers-series-9-pro-plus-02.avif" alt="Series 9 Pro Plus">
                    <h3>Series 9 Pro+</h3>
                    <p>五加一修剪元件，搭配 ProLift 提毛修剪器，完美處理濃密鬍渣。</p>
                </article>
                <article class="card">
                    <img src="/img/home-crosslink-series-7-70.avif" alt="Series 7">
                    <h3>Series 7</h3>
                    <p>360° 自適應刀頭，剃得更乾淨也更溫和，適合日常使用。</p>
                </article>
                <article class="card">
                    <img src="/img/Braun-mini_TOP-710842.avif" alt="Mini 剃鬚刀">
                    <h3>Mini 剃鬚刀</h3>
                    <p>高效、便攜，隨時隨地都能保持清爽整潔。</p>
                </article>
            </div>
        </section>

        <section id="gallery" class="section">
            <h2>圖片展示</h2>
            <div class="gallery">
                <div class="gallery-item">
                    <img src="/img/articles_beautiful-skin.avif" alt="美肌與剃鬍相關內容">
                    <div class="caption">美肌與剃鬍技巧指南</div>
                </div>
                <div class="gallery-item">
                    <img src="/img/articles_replacement-parts.avif" alt="更換零件">
                    <div class="caption">保養與更換零件</div>
                </div>
                <div class="gallery-item">
                    <img src="/img/facial-hair-styles-card-image.avif" alt="鬍型風格">
                    <div class="caption">多樣鬍型設計靈感</div>
                </div>
                <div class="gallery-item">
                    <img src="/img/home-crosslink-beard-trimmers.avif" alt="鬍鬚修剪器">
                    <div class="caption">修剪器與細節打造</div>
                </div>
            </div>
        </section>

        <section id="support" class="section">
            <h2>常見問題</h2>
            <div class="faq-item"><strong>電鬍刀濕刮還是乾刮比較好？</strong><br>兩者都可以，濕刮時搭配剃鬍膏會更順滑。</div>
            <div class="faq-item"><strong>多久該更換刀頭？</strong><br>建議每 12 至 18 個月更換，視使用頻率而定。</div>
            <div class="faq-item"><strong>如何清潔電鬍刀？</strong><br>每次使用後清除毛屑，並定期用清潔刷與水清洗。</div>
        </section>
    </div>

    <footer>
        © 2026 Braun 產品展示頁 • 使用 Flask 製作
    </footer>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

