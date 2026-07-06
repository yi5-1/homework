// Web 多人射擊客戶端 (Canvas + WebSocket)

// ====== 常數（要跟 server 的 constants.py 一致）======
const WORLD_W = 2000, WORLD_H = 2000;
const PLAYER_SIZE = 16;
const MAX_HP = 100;
const MOVE_SPEED = 260;
const SPEED_BUFF_MULT = 1.7;
const BULLET_RADIUS = 5;
const PICKUP_RADIUS = 14;
const ORBIT_BULLET_RADIUS = 7;
const MINIMAP_SIZE = 200;
const CHAT_DURATION = 5;
const CHAT_LOG_SHOW = 7;
const CHAT_PANEL_W = 340, CHAT_PANEL_H = 220;
const KILL_FEED_SHOW = 5;
const KILL_FEED_DURATION = 6;
const SUPER_PREFIX = "[卍煞氣a傳說卍]";

const BULLET_TIER_COLORS = [
  'rgb(255,80,20)', 'rgb(255,140,60)', 'rgb(255,210,60)',
  'rgb(80,220,80)', 'rgb(60,220,220)', 'rgb(80,120,255)',
  'rgb(200,100,220)', 'rgb(255,100,180)', 'rgb(220,40,40)',
  'rgb(255,215,0)'
];
const BULLET_TIER_SIZES = [5,6,7,8,9,10,11,12,14,16];

const BUFF_COLORS = {
  hp:     'rgb(100,220,100)',
  rapid:  'rgb(255,140,40)',
  speed:  'rgb(60,200,220)',
  orbit:  'rgb(200,100,220)',
  homing: 'rgb(240,220,60)'
};
const BUFF_LABELS = { hp: '+', rapid: 'R', speed: 'S', orbit: 'O', homing: 'H' };
const BUFF_ZH = { rapid: '快速射擊', speed: '加速移動', orbit: '軌道護盾', homing: '追蹤子彈' };

// ====== 全域狀態 ======
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
let W = 0, H = 0;

function resize() {
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

let ws = null;
let joined = false;
let myConfig = null;
let myX = WORLD_W / 2, myY = WORLD_H / 2;
let serverState = { players: [], bullets: [], pickups: [], orbits: [], chat_log: [], kill_feed: [], now: 0 };
let mouseX = 0, mouseY = 0;
let mouseDown = false;
let keys = {};
let chatActive = false;
let serverTimeOffset = 0;  // 用來把 client 時間對齊 server

// ====== 大廳 ======
function setupPicker(pickerId) {
  const els = document.querySelectorAll(`#${pickerId} .opt`);
  els.forEach(d => d.addEventListener('click', () => {
    els.forEach(x => x.classList.remove('sel'));
    d.classList.add('sel');
  }));
}
setupPicker('shape-picker');
setupPicker('color-picker');
document.getElementById('id-input').focus();

function getSelected(pickerId) {
  return document.querySelector(`#${pickerId} .opt.sel`).dataset.v;
}

function connect() {
  const id = document.getElementById('id-input').value.trim();
  if (!id) {
    document.getElementById('id-input').focus();
    return;
  }
  myConfig = {
    id: id.substring(0, 12),
    shape: getSelected('shape-picker'),
    color: getSelected('color-picker').split(',').map(Number),
  };
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${proto}//${location.host}/ws`);
  ws.onopen = () => {
    ws.send(JSON.stringify({ type: 'join', ...myConfig }));
    document.getElementById('lobby').classList.add('hidden');
    joined = true;
    canvas.focus();
  };
  ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data);
      if (msg.type === 'state') {
        serverState = msg;
        // 對齊 client 時鐘：offset = server_now - client_now
        serverTimeOffset = msg.now - (Date.now() / 1000);
      }
    } catch (err) {}
  };
  ws.onclose = () => {
    joined = false;
    showBanner('連線中斷，重新整理頁面');
  };
  ws.onerror = () => {
    showBanner('連線失敗');
  };
}

document.getElementById('connect-btn').addEventListener('click', connect);
document.getElementById('id-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') connect();
});

function showBanner(text) {
  const b = document.getElementById('banner');
  b.textContent = text;
  b.style.display = 'block';
}

function send(msg) {
  if (ws && ws.readyState === 1) {
    ws.send(JSON.stringify(msg));
  }
}

function findMe() {
  if (!myConfig) return null;
  return serverState.players.find(p => p.id === myConfig.id);
}

// ====== 輸入 ======
canvas.addEventListener('mousemove', (e) => {
  const r = canvas.getBoundingClientRect();
  mouseX = e.clientX - r.left;
  mouseY = e.clientY - r.top;
});
canvas.addEventListener('mousedown', (e) => {
  if (e.button === 0) mouseDown = true;
});
window.addEventListener('mouseup', (e) => {
  if (e.button === 0) mouseDown = false;
});
canvas.addEventListener('contextmenu', (e) => e.preventDefault());

document.addEventListener('keydown', (e) => {
  if (!joined) return;
  if (chatActive) return;   // 打字時所有按鍵不觸發移動
  if (e.key === 'Enter') {
    const me = findMe();
    if (me && me.alive) {
      chatActive = true;
      const ci = document.getElementById('chat-input');
      ci.style.display = 'block';
      ci.value = '';
      ci.focus();
    } else {
      // 已死亡 → Enter 重生
      send({ type: 'respawn' });
    }
    e.preventDefault();
    return;
  }
  keys[e.key.toLowerCase()] = true;
  if (['w','a','s','d',' '].includes(e.key.toLowerCase())) e.preventDefault();
});
document.addEventListener('keyup', (e) => {
  keys[e.key.toLowerCase()] = false;
});

const chatInput = document.getElementById('chat-input');
chatInput.addEventListener('keydown', (e) => {
  // 在 IME 組字時放行，只在真正 commit 後才處理 Enter
  if (e.isComposing || e.keyCode === 229) return;
  if (e.key === 'Enter') {
    const t = chatInput.value.trim();
    if (t) send({ type: 'chat', text: t });
    chatInput.value = '';
    chatInput.style.display = 'none';
    chatActive = false;
    keys = {};   // 清鍵位避免打完字後角色亂衝
    canvas.focus();
    e.preventDefault();
  } else if (e.key === 'Escape') {
    chatInput.value = '';
    chatInput.style.display = 'none';
    chatActive = false;
    keys = {};
  }
});

// ====== 繪圖工具 ======
function hsv2rgb(h, s, v) {
  const i = Math.floor(h * 6);
  const f = h * 6 - i;
  const p = v * (1 - s);
  const q = v * (1 - f * s);
  const t = v * (1 - (1 - f) * s);
  let r, g, b;
  switch (i % 6) {
    case 0: r = v; g = t; b = p; break;
    case 1: r = q; g = v; b = p; break;
    case 2: r = p; g = v; b = t; break;
    case 3: r = p; g = q; b = v; break;
    case 4: r = t; g = p; b = v; break;
    case 5: r = v; g = p; b = q; break;
  }
  return `rgb(${(r * 255) | 0}, ${(g * 255) | 0}, ${(b * 255) | 0})`;
}

function rainbow(t, offset = 0) {
  return hsv2rgb((t * 1.2 + offset) % 1, 1, 1);
}

function polygonPath(cx, cy, n, r, rot = 0) {
  ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const a = rot + 2 * Math.PI * i / n;
    const x = cx + r * Math.cos(a);
    const y = cy + r * Math.sin(a);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.closePath();
}

function starPath(cx, cy, spikes, outer, inner, rot = 0) {
  ctx.beginPath();
  for (let i = 0; i < spikes * 2; i++) {
    const r = i % 2 === 0 ? outer : inner;
    const a = rot + Math.PI * i / spikes;
    const x = cx + r * Math.cos(a);
    const y = cy + r * Math.sin(a);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.closePath();
}

function drawBulletByTier(sx, sy, tier, now) {
  const col = BULLET_TIER_COLORS[tier];
  const size = BULLET_TIER_SIZES[tier];
  const rot = now * 3;

  ctx.fillStyle = col;
  ctx.strokeStyle = 'black';
  ctx.lineWidth = 1;

  if (tier === 0) {
    ctx.beginPath(); ctx.arc(sx, sy, size, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  } else if (tier === 1) {
    ctx.beginPath(); ctx.arc(sx, sy, size, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = 'white';
    ctx.beginPath(); ctx.arc(sx, sy, size - 3, 0, Math.PI * 2); ctx.fill();
  } else if (tier === 2) {
    ctx.fillRect(sx - size, sy - size, size * 2, size * 2);
    ctx.strokeRect(sx - size, sy - size, size * 2, size * 2);
  } else if (tier === 3) {
    polygonPath(sx, sy, 3, size, rot); ctx.fill();
  } else if (tier === 4) {
    polygonPath(sx, sy, 4, size, rot); ctx.fill();
  } else if (tier === 5) {
    polygonPath(sx, sy, 5, size, rot); ctx.fill();
  } else if (tier === 6) {
    polygonPath(sx, sy, 6, size, rot); ctx.fill();
  } else if (tier === 7) {
    starPath(sx, sy, 5, size, size / 2, rot); ctx.fill();
  } else if (tier === 8) {
    starPath(sx, sy, 6, size, size / 2, rot); ctx.fill();
    ctx.strokeStyle = 'white'; ctx.lineWidth = 2;
    starPath(sx, sy, 6, size, size / 2, rot); ctx.stroke();
  } else {  // 9 傳說金
    ctx.fillStyle = 'rgba(255,240,100,0.35)';
    ctx.beginPath(); ctx.arc(sx, sy, size * 2, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = col;
    starPath(sx, sy, 5, size, size / 2, rot); ctx.fill();
    ctx.strokeStyle = 'white'; ctx.lineWidth = 2;
    starPath(sx, sy, 5, size, size / 2, rot); ctx.stroke();
  }
}

function drawShape(shape, col, sx, sy, size) {
  const [r, g, b] = col;
  ctx.fillStyle = `rgb(${r},${g},${b})`;
  ctx.strokeStyle = 'black';
  ctx.lineWidth = 2;
  if (shape === 'circle') {
    ctx.beginPath(); ctx.arc(sx, sy, size, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  } else if (shape === 'square') {
    ctx.fillRect(sx - size, sy - size, size * 2, size * 2);
    ctx.strokeRect(sx - size, sy - size, size * 2, size * 2);
  } else if (shape === 'triangle') {
    ctx.beginPath();
    ctx.moveTo(sx, sy - size);
    ctx.lineTo(sx - size, sy + size);
    ctx.lineTo(sx + size, sy + size);
    ctx.closePath();
    ctx.fill(); ctx.stroke();
  }
}

function drawHpBar(sx, sy, hp, size, max_hp) {
  const w = Math.max(40, size * 2 + 8), h = 5;
  const x = sx - w / 2, y = sy - size - 12;
  ctx.fillStyle = 'rgb(60,0,0)';
  ctx.fillRect(x, y, w, h);
  ctx.fillStyle = 'rgb(60,200,60)';
  ctx.fillRect(x, y, w * (hp / max_hp), h);
  ctx.strokeStyle = 'black'; ctx.lineWidth = 1;
  ctx.strokeRect(x + 0.5, y + 0.5, w, h);
}

function drawBubble(sx, sy, text, size) {
  if (!text) return;
  ctx.font = "14px 'Microsoft JhengHei', sans-serif";
  const tw = ctx.measureText(text).width;
  const pad = 6, h = 22;
  const bx = sx - tw / 2 - pad;
  const by = sy - size - 30 - h;
  ctx.fillStyle = 'white';
  ctx.strokeStyle = 'black'; ctx.lineWidth = 2;
  roundRect(bx, by, tw + pad * 2, h, 8, true, true);
  // tip
  ctx.beginPath();
  ctx.moveTo(sx - 5, by + h);
  ctx.lineTo(sx + 5, by + h);
  ctx.lineTo(sx,     by + h + 6);
  ctx.closePath();
  ctx.fillStyle = 'white'; ctx.fill();
  ctx.beginPath();
  ctx.moveTo(sx - 5, by + h); ctx.lineTo(sx, by + h + 6);
  ctx.moveTo(sx + 5, by + h); ctx.lineTo(sx, by + h + 6);
  ctx.strokeStyle = 'black'; ctx.stroke();

  ctx.fillStyle = 'black';
  ctx.fillText(text, bx + pad, by + h - 6);
}

function roundRect(x, y, w, h, r, fill, stroke) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
  if (fill) ctx.fill();
  if (stroke) ctx.stroke();
}

function drawPickup(sx, sy, ptype) {
  const col = BUFF_COLORS[ptype] || 'rgb(200,200,200)';
  ctx.fillStyle = col;
  ctx.beginPath(); ctx.arc(sx, sy, PICKUP_RADIUS, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = 'black'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(sx, sy, PICKUP_RADIUS, 0, Math.PI * 2); ctx.stroke();
  if (ptype === 'hp') {
    ctx.fillStyle = 'white';
    ctx.fillRect(sx - 2, sy - 7, 4, 14);
    ctx.fillRect(sx - 7, sy - 2, 14, 4);
  } else {
    ctx.fillStyle = 'black';
    ctx.font = "bold 14px sans-serif";
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(BUFF_LABELS[ptype] || '?', sx, sy);
    ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  }
}

// ====== 主迴圈 ======
let lastFrame = performance.now();

function frame(nowMs) {
  const dt = Math.min((nowMs - lastFrame) / 1000, 0.1);
  lastFrame = nowMs;
  const now = Date.now() / 1000 + serverTimeOffset;   // server-aligned time

  if (joined) {
    const me = findMe();
    const alive = !me || me.alive;
    const buffs = (me && me.buffs) || {};
    const has_speed = (buffs.speed > 0) || (me && me.speed_forever);
    const speed = MOVE_SPEED * (has_speed ? SPEED_BUFF_MULT : 1);

    // 移動
    if (alive && !chatActive) {
      let vx = 0, vy = 0;
      if (keys['w']) vy -= 1;
      if (keys['s']) vy += 1;
      if (keys['a']) vx -= 1;
      if (keys['d']) vx += 1;
      if (vx || vy) {
        const len = Math.hypot(vx, vy);
        myX = Math.max(0, Math.min(WORLD_W, myX + vx / len * speed * dt));
        myY = Math.max(0, Math.min(WORLD_H, myY + vy / len * speed * dt));
      }
      send({ type: 'update', x: myX, y: myY });
    } else if (me) {
      myX = me.x; myY = me.y;
    }

    // 射擊
    if (alive && !chatActive && mouseDown) {
      const dx = mouseX - W / 2, dy = mouseY - H / 2;
      if (dx * dx + dy * dy > 4) send({ type: 'shoot', dx, dy });
    }

    render(me, alive, buffs, now);
  }

  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// ====== 渲染 ======
function render(me, alive, buffs, now) {
  const camX = myX - W / 2, camY = myY - H / 2;

  // 背景 + 格線
  ctx.fillStyle = 'rgb(240,240,220)';
  ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = 'rgb(210,210,190)';
  ctx.lineWidth = 1;
  const grid = 100;
  const gx0 = ((-camX) % grid + grid) % grid;
  const gy0 = ((-camY) % grid + grid) % grid;
  for (let x = gx0; x < W; x += grid) {
    ctx.beginPath(); ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, H); ctx.stroke();
  }
  for (let y = gy0; y < H; y += grid) {
    ctx.beginPath(); ctx.moveTo(0, y + 0.5); ctx.lineTo(W, y + 0.5); ctx.stroke();
  }

  // 世界邊界
  ctx.strokeStyle = 'rgb(150,150,150)'; ctx.lineWidth = 3;
  ctx.strokeRect(-camX, -camY, WORLD_W, WORLD_H);

  // 道具
  for (const pk of serverState.pickups) {
    const sx = pk.x - camX, sy = pk.y - camY;
    if (sx > -50 && sx < W + 50 && sy > -50 && sy < H + 50) {
      drawPickup(sx, sy, pk.type);
    }
  }

  // 玩家
  ctx.font = "14px 'Microsoft JhengHei', sans-serif";
  for (const p of serverState.players) {
    const psize = PLAYER_SIZE + (p.size_bonus || 0);
    const sx = p.x - camX, sy = p.y - camY;
    if (sx < -80 || sx > W + 80 || sy < -80 || sy > H + 80) continue;

    if (p.alive) {
      drawShape(p.shape, p.color, sx, sy, psize);
      drawHpBar(sx, sy, p.hp, psize, p.max_hp || MAX_HP);
    } else {
      ctx.strokeStyle = 'rgb(120,120,120)'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(sx, sy, psize, 0, Math.PI * 2); ctx.stroke();
      ctx.fillStyle = 'rgb(120,120,120)';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('X_X', sx, sy);
      ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
    }

    // 名字（Lv + super 前綴 + 彩虹閃爍）
    const lv = p.level || 1;
    let name = `Lv${lv} ${p.id}`;
    if (p.super) name = SUPER_PREFIX + name;
    ctx.fillStyle = p.super ? rainbow(now, (Math.abs(hashStr(p.id)) % 100) / 100) : 'black';
    ctx.textAlign = 'center';
    ctx.fillText(name, sx, sy + psize + 18);
    ctx.textAlign = 'left';

    if (p.chat && now - (p.chat_time || 0) < CHAT_DURATION) {
      drawBubble(sx, sy, p.chat, psize);
    }
  }

  // 軌道護盾彈丸
  for (const o of serverState.orbits) {
    const sx = o.x - camX, sy = o.y - camY;
    if (sx > -50 && sx < W + 50 && sy > -50 && sy < H + 50) {
      const [r, g, b] = o.color;
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.beginPath(); ctx.arc(sx, sy, ORBIT_BULLET_RADIUS, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'white'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(sx, sy, ORBIT_BULLET_RADIUS, 0, Math.PI * 2); ctx.stroke();
    }
  }

  // 子彈
  for (const b of serverState.bullets) {
    const sx = b.x - camX, sy = b.y - camY;
    if (sx < -60 || sx > W + 60 || sy < -60 || sy > H + 60) continue;
    if (b.rainbow) {
      ctx.fillStyle = rainbow(now, b.x * 0.01 + b.y * 0.01);
      ctx.beginPath(); ctx.arc(sx, sy, BULLET_RADIUS + 2, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = 'white';
      ctx.beginPath(); ctx.arc(sx, sy, BULLET_RADIUS - 1, 0, Math.PI * 2); ctx.fill();
    } else {
      if (b.homing) {
        ctx.fillStyle = 'rgb(240,220,60)';
        ctx.beginPath();
        ctx.arc(sx, sy, BULLET_TIER_SIZES[b.tier || 0] + 2, 0, Math.PI * 2);
        ctx.fill();
      }
      drawBulletByTier(sx, sy, b.tier || 0, now);
    }
  }

  // 準心
  if (alive) {
    ctx.strokeStyle = 'black'; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(mouseX - 12, mouseY); ctx.lineTo(mouseX - 3, mouseY);
    ctx.moveTo(mouseX + 3, mouseY);  ctx.lineTo(mouseX + 12, mouseY);
    ctx.moveTo(mouseX, mouseY - 12); ctx.lineTo(mouseX, mouseY - 3);
    ctx.moveTo(mouseX, mouseY + 3);  ctx.lineTo(mouseX, mouseY + 12);
    ctx.stroke();
    ctx.fillStyle = 'red';
    ctx.beginPath(); ctx.arc(mouseX, mouseY, 2, 0, Math.PI * 2); ctx.fill();
  }

  // 小地圖
  const mmX = 10, mmY = H - MINIMAP_SIZE - 10;
  ctx.fillStyle = 'rgb(30,30,30)';
  ctx.fillRect(mmX, mmY, MINIMAP_SIZE, MINIMAP_SIZE);
  ctx.strokeStyle = 'white'; ctx.lineWidth = 2;
  ctx.strokeRect(mmX, mmY, MINIMAP_SIZE, MINIMAP_SIZE);
  const vsx = mmX + camX * MINIMAP_SIZE / WORLD_W;
  const vsy = mmY + camY * MINIMAP_SIZE / WORLD_H;
  const vsw = W * MINIMAP_SIZE / WORLD_W;
  const vsh = H * MINIMAP_SIZE / WORLD_H;
  ctx.strokeStyle = 'yellow'; ctx.lineWidth = 1;
  ctx.strokeRect(vsx, vsy, vsw, vsh);
  for (const pk of serverState.pickups) {
    ctx.fillStyle = BUFF_COLORS[pk.type] || 'gray';
    ctx.beginPath();
    ctx.arc(mmX + pk.x * MINIMAP_SIZE / WORLD_W, mmY + pk.y * MINIMAP_SIZE / WORLD_H, 3, 0, Math.PI * 2);
    ctx.fill();
  }
  for (const p of serverState.players) {
    if (!p.alive) continue;
    const [r, g, b] = p.color;
    ctx.fillStyle = `rgb(${r},${g},${b})`;
    ctx.beginPath();
    ctx.arc(mmX + p.x * MINIMAP_SIZE / WORLD_W, mmY + p.y * MINIMAP_SIZE / WORLD_H, 3, 0, Math.PI * 2);
    ctx.fill();
  }

  // HUD: HP + XP + 傷害
  if (me) {
    const max_hp = me.max_hp || MAX_HP;
    // HP bar
    ctx.fillStyle = 'rgb(60,0,0)'; ctx.fillRect(10, 10, 320, 26);
    ctx.fillStyle = 'rgb(60,200,60)'; ctx.fillRect(10, 10, 320 * me.hp / max_hp, 26);
    ctx.strokeStyle = 'white'; ctx.lineWidth = 2; ctx.strokeRect(10, 10, 320, 26);
    ctx.fillStyle = 'white'; ctx.font = "14px 'Microsoft JhengHei', sans-serif";
    ctx.fillText(`HP ${Math.floor(me.hp)} / ${max_hp}`, 16, 28);

    // XP bar
    ctx.fillStyle = 'rgb(30,30,60)'; ctx.fillRect(10, 40, 320, 14);
    if (me.xp_need > 0) {
      ctx.fillStyle = 'rgb(80,180,255)';
      ctx.fillRect(10, 40, 320 * me.xp / me.xp_need, 14);
    } else {
      ctx.fillStyle = 'rgb(255,215,0)';
      ctx.fillRect(10, 40, 320, 14);
    }
    ctx.strokeStyle = 'white'; ctx.lineWidth = 1; ctx.strokeRect(10, 40, 320, 14);
    ctx.font = "12px 'Microsoft JhengHei', sans-serif";
    ctx.fillStyle = 'white';
    const xpLbl = me.xp_need > 0
      ? `Lv ${me.level}   XP ${me.xp} / ${me.xp_need}   DMG ${me.damage}`
      : `Lv ${me.level} MAX`;
    ctx.fillText(xpLbl, 16, 51);
  }

  // Buff 列表
  if (me) {
    let y = 60;
    function buffRow(color, text) {
      ctx.fillStyle = color;
      ctx.beginPath(); ctx.arc(20, y + 10, 9, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'black'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(20, y + 10, 9, 0, Math.PI * 2); ctx.stroke();
      ctx.font = "14px 'Microsoft JhengHei', sans-serif";
      const tw = ctx.measureText(text).width;
      ctx.fillStyle = 'rgba(0,0,0,0.55)';
      ctx.fillRect(32, y + 2, tw + 8, 20);
      ctx.fillStyle = 'white';
      ctx.fillText(text, 36, y + 17);
      y += 22;
    }
    if (me.rapid_forever) buffRow(BUFF_COLORS.rapid, '快速射擊  ∞');
    if (me.speed_forever) buffRow(BUFF_COLORS.speed, '加速移動  ∞');
    for (const [name, remaining] of Object.entries(me.buffs || {})) {
      if (name === 'hp' || remaining <= 0) continue;
      buffRow(BUFF_COLORS[name] || 'gray', `${BUFF_ZH[name] || name}  ${remaining.toFixed(1)}s`);
    }
  }

  // 線上人數
  ctx.font = "14px 'Microsoft JhengHei', sans-serif";
  ctx.fillStyle = 'black';
  ctx.textAlign = 'right';
  ctx.fillText(`線上：${serverState.players.length}`, W - 10, 24);
  ctx.textAlign = 'left';

  // 擊殺公告
  const visible = serverState.kill_feed.slice(-KILL_FEED_SHOW).filter(
    k => (now - (k.ts || 0)) < KILL_FEED_DURATION
  );
  let fy = 34;
  for (const k of visible.slice().reverse()) {
    const age = now - (k.ts || 0);
    const alpha = age < KILL_FEED_DURATION - 1 ? 1 : Math.max(0, (KILL_FEED_DURATION - age));
    ctx.globalAlpha = alpha;
    const killerName = (k.killer_super ? SUPER_PREFIX : '') + (k.killer || '?');
    const victimName = (k.victim_super ? SUPER_PREFIX : '') + (k.victim || '?');
    ctx.font = "14px 'Microsoft JhengHei', sans-serif";
    const wKill = ctx.measureText(killerName).width;
    const wMid  = ctx.measureText(' 擊殺了 ').width;
    const wVic  = ctx.measureText(victimName).width;
    const tw = wKill + wMid + wVic + 16;
    ctx.fillStyle = `rgba(0,0,0,${Math.min(0.7, alpha * 0.7)})`;
    ctx.fillRect(W - tw - 10, fy, tw, 24);
    let x = W - tw - 10 + 8;
    const [kr, kg, kb] = k.killer_color || [220, 60, 60];
    ctx.fillStyle = `rgb(${kr},${kg},${kb})`;
    ctx.fillText(killerName, x, fy + 17); x += wKill;
    ctx.fillStyle = 'white';
    ctx.fillText(' 擊殺了 ', x, fy + 17); x += wMid;
    const [vr, vg, vb] = k.victim_color || [60, 60, 220];
    ctx.fillStyle = `rgb(${vr},${vg},${vb})`;
    ctx.fillText(victimName, x, fy + 17);
    fy += 28;
    ctx.globalAlpha = 1;
  }

  // 右下聊天視窗
  const px = W - CHAT_PANEL_W - 10, py = H - CHAT_PANEL_H - 10;
  ctx.fillStyle = 'rgba(0,0,0,0.5)';
  ctx.fillRect(px, py, CHAT_PANEL_W, CHAT_PANEL_H);
  ctx.strokeStyle = 'white'; ctx.lineWidth = 1;
  ctx.strokeRect(px, py, CHAT_PANEL_W, CHAT_PANEL_H);
  ctx.font = "14px 'Microsoft JhengHei', sans-serif";
  ctx.fillStyle = 'white';
  const msgs = serverState.chat_log.slice(-CHAT_LOG_SHOW);
  let ty = py + 20;
  for (const m of msgs) {
    let line = `[${m.author || '?'}] ${m.text || ''}`;
    while (ctx.measureText(line + '…').width > CHAT_PANEL_W - 16 && line.length > 3) {
      line = line.slice(0, -1);
    }
    ctx.fillText(line, px + 8, ty);
    ty += 20;
  }

  // GameOver
  if (me && !me.alive) {
    ctx.fillStyle = 'rgba(0,0,0,0.6)';
    ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = 'rgb(255,60,60)';
    ctx.font = "bold 72px 'Microsoft JhengHei', sans-serif";
    ctx.textAlign = 'center';
    ctx.fillText('GAME OVER', W / 2, H / 2 - 30);
    ctx.fillStyle = 'white';
    ctx.font = "bold 32px 'Microsoft JhengHei', sans-serif";
    ctx.fillText('按 Enter 重生', W / 2, H / 2 + 40);
    ctx.textAlign = 'left';
  }
}

function hashStr(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h << 5) - h + s.charCodeAt(i);
    h |= 0;
  }
  return h;
}
