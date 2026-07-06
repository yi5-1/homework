// ─── 登入/註冊 Modal ─────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    checkAuth();
});

function checkAuth() {
    fetch('/api/me')
        .then(r => r.json())
        .then(data => {
            const nameEl = document.getElementById('nav-username');
            const logoutBtn = document.getElementById('btn-logout');
            const loginBtn = document.getElementById('btn-login');
            if (data.ok) {
                nameEl.textContent = '👤 ' + data.user.username;
                nameEl.style.display = 'inline';
                logoutBtn.style.display = 'inline';
                if (loginBtn) loginBtn.style.display = 'none';
            } else {
                nameEl.style.display = 'none';
                logoutBtn.style.display = 'none';
                if (loginBtn) loginBtn.style.display = 'inline';
            }
        });
}

function logout() {
    fetch('/api/logout', { method: 'POST' })
        .then(() => { window.location.reload(); });
}

// ─── 加入購物車 ─────────────────────────────

function addToCart(productId) {
    fetch('/api/cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, quantity: 1 })
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            alert('已加入購物車');
        } else {
            alert(data.message);
            if (!data.ok && data.message === '請先登入') {
                window.location.href = '/products';
            }
        }
    });
}

// ─── 使用者登入 Modal ─────────────────────────

function showLoginModal() {
    const html = `
        <div id="login-modal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;z-index:999">
            <div style="background:#fff;border-radius:16px;padding:2rem;width:360px;max-width:90%">
                <h2 style="margin-bottom:1rem">登入 / 註冊</h2>
                <div class="form-group">
                    <label>帳號</label>
                    <input type="text" id="modal-username" style="width:100%;padding:0.6rem;border:1px solid #d2d2d7;border-radius:8px">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="modal-email" style="width:100%;padding:0.6rem;border:1px solid #d2d2d7;border-radius:8px">
                </div>
                <div class="form-group">
                    <label>密碼</label>
                    <input type="password" id="modal-password" style="width:100%;padding:0.6rem;border:1px solid #d2d2d7;border-radius:8px">
                </div>
                <div style="display:flex;gap:0.5rem;margin-top:1rem">
                    <button class="btn btn-primary" onclick="doRegister()">註冊</button>
                    <button class="btn" onclick="doLogin()" style="background:#e8e8ed">登入</button>
                    <button class="btn" onclick="closeLoginModal()" style="margin-left:auto;background:transparent">關閉</button>
                </div>
                <div id="modal-msg" style="margin-top:0.5rem"></div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
}

function closeLoginModal() {
    const el = document.getElementById('login-modal');
    if (el) el.remove();
}

function doRegister() {
    const username = document.getElementById('modal-username').value;
    const email = document.getElementById('modal-email').value;
    const password = document.getElementById('modal-password').value;
    fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    })
    .then(r => r.json())
    .then(data => {
        const msg = document.getElementById('modal-msg');
        if (data.ok) {
            msg.innerHTML = '<div class="alert alert-success">註冊成功！</div>';
            closeLoginModal();
            checkAuth();
        } else {
            msg.innerHTML = `<div class="alert alert-error">${data.message}</div>`;
        }
    });
}

function doLogin() {
    const username = document.getElementById('modal-username').value;
    const password = document.getElementById('modal-password').value;
    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(r => r.json())
    .then(data => {
        const msg = document.getElementById('modal-msg');
        if (data.ok) {
            msg.innerHTML = '<div class="alert alert-success">登入成功！</div>';
            closeLoginModal();
            checkAuth();
        } else {
            msg.innerHTML = `<div class="alert alert-error">${data.message}</div>`;
        }
    });
}
