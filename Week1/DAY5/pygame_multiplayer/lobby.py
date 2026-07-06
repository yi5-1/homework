# 大廳畫面：用滑鼠/Tab 選 Server IP、ID、造型、顏色
# show_lobby() 回傳 dict {"ip","id","shape","color"}，若視窗被關閉則回傳 None
# 支援：中文 ID 輸入、Tab 切換欄位、Enter 確認

import pygame
from constants import SCREEN_W, SCREEN_H, SHAPES, COLORS


def show_lobby():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED)
    pygame.display.set_caption("加入遊戲")
    try:
        font  = pygame.font.SysFont("Microsoft JhengHei", 20)
        big   = pygame.font.SysFont("Microsoft JhengHei", 34, bold=True)
        small = pygame.font.SysFont("Microsoft JhengHei", 15)
    except Exception:
        font  = pygame.font.Font(None, 22)
        big   = pygame.font.Font(None, 38)
        small = pygame.font.Font(None, 17)
    clock = pygame.time.Clock()
    pygame.key.stop_text_input()

    # 狀態
    ip_text   = "192.168.1.101"
    id_text   = ""
    shape_idx = 0
    color_idx = 0
    focus     = "ip"          # 一開始就 focus 在 IP，可以直接 Tab 切
    pygame.key.start_text_input()

    # 版面
    left = SCREEN_W // 2 - 200
    ip_rect      = pygame.Rect(left + 100, 160, 400, 40)
    id_rect      = pygame.Rect(left + 100, 230, 400, 40)
    shape_rects  = [pygame.Rect(left + 100 + i * 100, 320, 80, 80) for i in range(len(SHAPES))]
    color_rects  = [pygame.Rect(left + 100 + i * 70,  440, 60, 60) for i in range(len(COLORS))]
    connect_rect = pygame.Rect(SCREEN_W // 2 - 100, 570, 200, 60)

    caret_ts = 0

    def try_submit():
        if ip_text.strip() and id_text.strip():
            pygame.key.stop_text_input()
            return {
                "ip":    ip_text.strip(),
                "id":    id_text.strip()[:12],
                "shape": SHAPES[shape_idx],
                "color": COLORS[color_idx][1],
            }
        return None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if ip_rect.collidepoint(mx, my):
                    focus = "ip"
                    pygame.key.start_text_input()
                elif id_rect.collidepoint(mx, my):
                    focus = "id"
                    pygame.key.start_text_input()
                else:
                    for i, r in enumerate(shape_rects):
                        if r.collidepoint(mx, my):
                            shape_idx = i
                    for i, r in enumerate(color_rects):
                        if r.collidepoint(mx, my):
                            color_idx = i
                    if connect_rect.collidepoint(mx, my):
                        r = try_submit()
                        if r:
                            return r

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    focus = "id" if focus == "ip" else "ip"
                    pygame.key.start_text_input()
                elif event.key == pygame.K_BACKSPACE:
                    if focus == "ip":
                        ip_text = ip_text[:-1]
                    elif focus == "id":
                        id_text = id_text[:-1]
                elif event.key == pygame.K_RETURN:
                    r = try_submit()
                    if r:
                        return r

            elif event.type == pygame.TEXTINPUT:
                if focus == "ip":
                    ip_text += event.text
                elif focus == "id":
                    id_text += event.text

        # ====== 繪製 ======
        screen.fill((28, 30, 46))

        title = big.render("加入遊戲", True, (255, 255, 255))
        screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 70))

        caret_on = (pygame.time.get_ticks() // 500) % 2 == 0

        def draw_field(label, rect, text, is_focus):
            screen.blit(font.render(label, True, (255, 255, 255)), (rect.x - 100, rect.y + 8))
            pygame.draw.rect(screen, (255, 255, 255), rect)
            border = (255, 220, 0) if is_focus else (140, 140, 150)
            pygame.draw.rect(screen, border, rect, 3)
            t = font.render(text, True, (0, 0, 0))
            screen.blit(t, (rect.x + 8, rect.y + 8))
            if is_focus and caret_on:
                cx = rect.x + 8 + t.get_width() + 1
                pygame.draw.line(screen, (0, 0, 0), (cx, rect.y + 8), (cx, rect.y + rect.h - 8), 2)

        draw_field("Server IP：", ip_rect, ip_text, focus == "ip")
        draw_field("你的 ID：",   id_rect, id_text, focus == "id")

        # 造型
        screen.blit(font.render("造型：", True, (255, 255, 255)), (shape_rects[0].x - 100, 350))
        for i, (name, r) in enumerate(zip(SHAPES, shape_rects)):
            pygame.draw.rect(screen, (55, 58, 78), r)
            pygame.draw.rect(screen, (255, 220, 0) if i == shape_idx else (140, 140, 150), r, 3)
            cx, cy = r.center
            col = tuple(COLORS[color_idx][1])
            if name == "circle":
                pygame.draw.circle(screen, col, (cx, cy), 25)
            elif name == "square":
                pygame.draw.rect(screen, col, (cx - 25, cy - 25, 50, 50))
            elif name == "triangle":
                pygame.draw.polygon(screen, col, [(cx, cy - 25), (cx - 25, cy + 25), (cx + 25, cy + 25)])

        # 顏色
        screen.blit(font.render("顏色：", True, (255, 255, 255)), (color_rects[0].x - 100, 460))
        for i, ((cname, col), r) in enumerate(zip(COLORS, color_rects)):
            pygame.draw.rect(screen, tuple(col), r)
            pygame.draw.rect(screen, (255, 220, 0) if i == color_idx else (140, 140, 150), r, 3)

        # 連線按鈕
        can_connect = ip_text.strip() != "" and id_text.strip() != ""
        btn_col = (50, 180, 80) if can_connect else (80, 80, 80)
        pygame.draw.rect(screen, btn_col, connect_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), connect_rect, 2, border_radius=8)
        t = font.render("連線 (Enter)", True, (255, 255, 255))
        screen.blit(t, (connect_rect.centerx - t.get_width() // 2,
                        connect_rect.centery - t.get_height() // 2))

        hint = small.render(
            "Tab 切換欄位  |  ID 支援中文  |  點欄位可直接輸入  |  F11 遊戲內全螢幕",
            True, (180, 180, 200)
        )
        screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 40))

        pygame.display.flip()
        clock.tick(60)
