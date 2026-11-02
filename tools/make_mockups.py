"""PPT에 넣을 설계 목업 이미지를 직접 그려 assets/presentation_examples/ 에 저장한다.

모든 그림은 우리 스프라이트와 도형으로 그린 설계 스케치이며 실제 게임 화면이 아니다.
실행: python tools/make_mockups.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SPR = os.path.join(ROOT, "assets", "sprites", "unified")
OUT = os.path.join(ROOT, "assets", "presentation_examples")
W, H = 1280, 720

NAVY = (15, 22, 35)
PANEL = (26, 36, 54)
CYAN = (79, 195, 247)
DCYAN = (40, 120, 160)
WARN = (255, 138, 101)
RED = (255, 90, 90)
SLATE = (74, 90, 117)
MID = (58, 124, 165)
TEXT = (232, 238, 247)
MUTED = (159, 176, 200)
GREEN = (124, 227, 161)

DEATH = (120, 40, 55)
ZONES = [("페이드", 0, 19, DEATH), ("노멀", 20, 49, MID), ("각성", 50, 89, CYAN),
         ("위험", 90, 99, WARN), ("", 100, 100, RED)]


FONT_SCALE = 1.22


def font(size, bold=True):
    name = "malgunbd.ttf" if bold else "malgun.ttf"
    return ImageFont.truetype(os.path.join("C:\\Windows\\Fonts", name), int(size * FONT_SCALE))


def sprite(name, k=3, flip=False):
    im = Image.open(os.path.join(SPR, f"{name}_idle.png")).convert("RGBA")
    im = im.resize((im.width * k, im.height * k), Image.NEAREST)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def new_canvas(top=(12, 18, 30), bottom=(24, 34, 54)):
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,))
    return img


def fog(img, n=14, color=(60, 120, 160), alpha=40, seed=1, ymin=0.35):
    rnd = random.Random(seed)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        cx, cy = rnd.randint(0, img.width), rnd.randint(int(img.height * ymin), img.height)
        rx, ry = rnd.randint(120, 320), rnd.randint(30, 90)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(40))
    img.alpha_composite(layer)


def glow(img, cx, cy, rx, ry, color, alpha=120, blur=30):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color + (alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))


def vignette(img, color, strength=150):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = min(60, img.width // 8 - 1, img.height // 6 - 1)
    for i in range(steps):
        a = int(strength * (1 - i / steps) ** 2)
        d.rectangle([i * 4, i * 3, img.width - i * 4, img.height - i * 3], outline=color + (a,), width=4)
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(12)))


def platform(img, x0, x1, y, thick=26):
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y, x1, y + thick], fill=(34, 46, 68))
    d.rectangle([x0, y, x1, y + 5], fill=(70, 100, 130))
    for x in range(x0, x1, 48):
        d.line([(x, y + 6), (x, y + thick)], fill=(26, 36, 54), width=2)


def bg_pillars(img, seed=3):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    for x in range(40, W, 210):
        h = rnd.randint(300, 460)
        d.rectangle([x, H - h, x + 70, H], fill=(18, 26, 42))
        for wy in range(H - h + 30, H - 60, 70):
            if rnd.random() < 0.35:
                d.rectangle([x + 22, wy, x + 48, wy + 22], fill=(30, 70, 96))


def paste_bottom(img, spr, x, ground_y, shadow=True):
    if shadow:
        ImageDraw.Draw(img).ellipse([x + 4, ground_y - 8, x + spr.width - 4, ground_y + 6], fill=(5, 8, 14, 150))
    img.alpha_composite(spr, (int(x), int(ground_y - spr.height)))


def label(img, text, x=28, y=None, size=20, color=MUTED):
    d = ImageDraw.Draw(img)
    y = H - 40 if y is None else y
    d.text((x, y), text, font=font(size, False), fill=color)


def tag(img, text="설계 목업 (실제 구현 화면 아님)"):
    label(img, text, 28, H - 38, 18, (120, 140, 170))


def zone_of(v):
    if v >= 100:
        return "오버로드", RED
    if v >= 90:
        return "위험", WARN
    if v >= 50:
        return "각성", CYAN
    if v >= 20:
        return "노멀", MID
    return "페이드", DEATH


def draw_gauge(img, x, y, w, h, value, labels=True, big=False):
    d = ImageDraw.Draw(img)
    total = 101
    for name, lo, hi, col in ZONES:
        x0 = x + w * lo / total
        x1 = x + w * (hi + 1) / total - 2
        dim = tuple(int(c * 0.35) for c in col)
        d.rectangle([x0, y, x1, y + h], fill=dim)
        filled = min(hi, value) - lo
        if value >= lo:
            fx = x0 + (x1 - x0) * min(1.0, (min(hi, value) - lo + 1) / (hi - lo + 1))
            d.rectangle([x0, y, fx, y + h], fill=col)
        if labels and name:
            d.text(((x0 + x1) / 2, y + h + 8), name, font=font(20 if big else 16), fill=col, anchor="ma")
            d.text(((x0 + x1) / 2, y + h + (34 if big else 28)), f"{lo}~{hi}%", font=font(16 if big else 13, False), fill=MUTED, anchor="ma")
    mx = x + w * value / total
    d.polygon([(mx - 9, y - 14), (mx + 9, y - 14), (mx, y - 2)], fill=TEXT)
    name, col = zone_of(value)
    d.text((mx, y - 20), f"{value}%", font=font(26 if big else 22), fill=col, anchor="md")
    d.rectangle([x - 2, y - 2, x + w + 2, y + h + 2], outline=(200, 215, 235), width=2)


def hud(img, gauge=50, hp=0.8, dash=2, dash_max=2, weapons=("파이프", "식칼"), active=0, enhanced=False, minimap=True):
    d = ImageDraw.Draw(img)
    # 체력
    d.text((28, 22), "HP", font=font(22), fill=TEXT)
    d.rectangle([76, 24, 316, 48], fill=(60, 24, 30), outline=(200, 215, 235), width=2)
    d.rectangle([78, 26, 78 + 236 * hp, 46], fill=RED)
    # 대시 슬롯
    d.text((28, 62), "대시", font=font(20), fill=MUTED)
    for i in range(dash_max):
        cx = 100 + i * 34
        col = CYAN if i < dash else (50, 64, 90)
        d.polygon([(cx, 64), (cx + 14, 78), (cx, 92), (cx - 14, 78)], fill=col, outline=(200, 215, 235))
    # 게이지
    d.text((290 if False else 400, 4), "헤이즈 게이지", font=font(15), fill=MUTED)
    draw_gauge(img, 400, 62, 480, 20, gauge, labels=True)
    # 무기 슬롯
    for i, name in enumerate(weapons):
        x0 = W - 250 + i * 110
        on = i == active
        d.rounded_rectangle([x0, H - 130, x0 + 96, H - 40], radius=10, fill=PANEL, outline=CYAN if on else SLATE, width=4 if on else 2)
        d.text((x0 + 48, H - 98), name, font=font(20), fill=TEXT if on else MUTED, anchor="mm")
        d.text((x0 + 48, H - 66), str(i + 1), font=font(18, False), fill=MUTED, anchor="mm")
        if on and enhanced:
            glow(img, x0 + 48, H - 85, 70, 55, CYAN, 90, 14)
            d.rounded_rectangle([x0, H - 130, x0 + 96, H - 40], radius=10, outline=CYAN, width=5)
    d.rounded_rectangle([W - 250, H - 170, W - 190, H - 140], radius=6, fill=PANEL, outline=CYAN)
    d.text((W - 220, H - 155), "E 강화", font=font(16), fill=CYAN, anchor="mm")
    # 재화 (헤이즈 조각)
    d.polygon([(W - 182, 168), (W - 168, 152), (W - 154, 168), (W - 168, 184)], fill=(180, 140, 255), outline=(220, 200, 255))
    d.text((W - 140, 168), "조각 12", font=font(18), fill=TEXT, anchor="lm")
    if minimap:
        mx, my = W - 190, 22
        d.rectangle([mx - 8, my - 8, mx + 170, my + 120], fill=(10, 16, 26, 210), outline=SLATE, width=2)
        cells = [(0, 1), (1, 1), (2, 1), (2, 0), (1, 2), (3, 1)]
        for cx, cy in cells:
            col = CYAN if (cx, cy) == (1, 1) else (60, 80, 110)
            d.rectangle([mx + cx * 40, my + cy * 34, mx + cx * 40 + 34, my + cy * 34 + 28], fill=col)


def crosshair(img, x, y, color=TEXT):
    d = ImageDraw.Draw(img)
    d.ellipse([x - 20, y - 20, x + 20, y + 20], outline=color, width=3)
    for dx, dy in ((-30, 0), (30, 0), (0, -30), (0, 30)):
        d.line([(x + dx // 3 * 1, y + dy // 3 * 1), (x + dx, y + dy)], fill=color, width=3)


def dmg(img, x, y, text, color=WARN, size=30):
    d = ImageDraw.Draw(img)
    d.text((x + 2, y + 2), text, font=font(size), fill=(0, 0, 0), anchor="mm")
    d.text((x, y), text, font=font(size), fill=color, anchor="mm")


def slash_arc(img, cx, cy, r, a0, a1, color=CYAN, width=14):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=color + (230,), width=width)
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(2)))


def arrow(d, x0, y0, x1, y1, color=TEXT, width=6, head=22):
    d.line([(x0, y0), (x1, y1)], fill=color, width=width)
    a = math.atan2(y1 - y0, x1 - x0)
    pts = [(x1, y1), (x1 - head * math.cos(a - 0.45), y1 - head * math.sin(a - 0.45)),
           (x1 - head * math.cos(a + 0.45), y1 - head * math.sin(a + 0.45))]
    d.polygon(pts, fill=color)


def finish(img):
    return img.convert("RGB")


# ---------------------------------------------------------------- 장면
def scene_title():
    img = new_canvas((8, 12, 24), (26, 40, 64))
    fog(img, 18, (70, 130, 170), 55, 11, 0.2)
    d = ImageDraw.Draw(img)
    # 중앙 탑 실루엣
    d.polygon([(560, 120), (720, 120), (700, 560), (580, 560)], fill=(14, 20, 34))
    d.rectangle([590, 70, 690, 130], fill=(14, 20, 34))
    d.polygon([(590, 70), (640, 20), (690, 70)], fill=(14, 20, 34))
    for y in range(160, 520, 60):
        d.rectangle([620, y, 660, y + 26], fill=(40, 100, 130))
    glow(img, 640, 90, 90, 60, CYAN, 110, 26)
    bg_pillars(img, 5)
    fog(img, 10, (90, 150, 190), 45, 12, 0.6)
    platform(img, 0, W, 600, 130)
    paste_bottom(img, sprite("n09", 4), 220, 600)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 300), "HAZE", font=font(150), fill=TEXT, anchor="mm", stroke_width=4, stroke_fill=(10, 20, 40))
    glow(img, W // 2, 300, 260, 70, CYAN, 70, 40)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 300), "HAZE", font=font(150), fill=TEXT, anchor="mm", stroke_width=3, stroke_fill=CYAN)
    d.text((W // 2, 410), "안개를 삼키고 탈출하라", font=font(34, False), fill=CYAN, anchor="mm")
    d.text((W // 2, 640), "PRESS ANY KEY", font=font(30), fill=MUTED, anchor="mm")
    tag(img, "제목 화면 설계 목업 (실제 구현 화면 아님)")
    return finish(img)


def scene_battle():
    img = new_canvas()
    bg_pillars(img)
    fog(img, 12, (60, 120, 160), 38, 2, 0.5)
    platform(img, 0, W, 620, 100)
    platform(img, 90, 430, 440)
    platform(img, 790, 1130, 370)
    paste_bottom(img, sprite("n09", 3), 230, 440)
    paste_bottom(img, sprite("enemy_guard", 3), 640, 620, True)
    paste_bottom(img, sprite("enemy_slum", 3), 930, 370, True)
    paste_bottom(img, sprite("enemy_hound", 3), 830, 620, True)
    # 문 (잠김)
    d = ImageDraw.Draw(img)
    d.rectangle([1200, 450, 1260, 620], fill=(30, 40, 60), outline=SLATE, width=4)
    d.text((1230, 535), "잠김", font=font(18), fill=RED, anchor="mm")
    slash_arc(img, 330, 300, 90, 300, 40, CYAN, 12)
    crosshair(img, 650, 400)
    dmg(img, 700, 330, "-24")
    dmg(img, 940, 220, "-12", WARN)
    hud(img, 62, 0.8, 2, 2, ("파이프", "식칼"), 0)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 175), "남은 적 3", font=font(26), fill=TEXT, anchor="mm")
    tag(img)
    return finish(img)


def scene_world_map():
    img = new_canvas((8, 12, 22), (18, 28, 46))
    d = ImageDraw.Draw(img)
    cx, cy = 400, 360
    rings = [(330, "제9구역 폐기물 슬럼", "안개 옅음", (46, 66, 92)),
             (225, "제4구역 철골 공장", "안개 보통", (36, 54, 80)),
             (120, "코어 감시자의 탑", "안개 짙음", (22, 36, 60))]
    for r, name, dens, col in rings:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=(110, 140, 170), width=3)
    fog_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog_layer)
    for r, a in ((120, 120), (225, 70), (330, 30)):
        fd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(79, 195, 247, a))
    img.alpha_composite(fog_layer.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(img)
    # 탑
    d.polygon([(cx - 26, cy + 44), (cx + 26, cy + 44), (cx + 16, cy - 40), (cx - 16, cy - 40)], fill=(10, 16, 28))
    d.polygon([(cx - 20, cy - 40), (cx, cy - 74), (cx + 20, cy - 40)], fill=(10, 16, 28))
    glow(img, cx, cy - 50, 30, 20, CYAN, 140, 12)
    d = ImageDraw.Draw(img)
    # 경로
    pts = [(cx - 300, cy + 130), (cx - 200, cy + 70), (cx - 150, cy + 10), (cx - 70, cy - 10), (cx, cy)]
    d.line(pts, fill=WARN, width=7)
    arrow(d, pts[-2][0], pts[-2][1], pts[-1][0] - 14, pts[-1][1] + 2, WARN, 7, 24)
    for (px, py), n in zip(pts[:3], ["START", "", ""]):
        d.ellipse([px - 11, py - 11, px + 11, py + 11], fill=WARN, outline=TEXT, width=3)
    d.text((pts[0][0] - 8, pts[0][1] + 28), "출발", font=font(20), fill=WARN, anchor="mm")
    d.text((cx, cy + 66), "탈출구", font=font(20), fill=CYAN, anchor="mm")
    # 범례
    x0 = 800
    d.text((x0, 90), "네뷸라 교도소 (약도)", font=font(34), fill=TEXT)
    for i, (r, name, dens, col) in enumerate(rings):
        y = 170 + i * 120
        d.rounded_rectangle([x0, y, x0 + 420, y + 96], radius=12, fill=PANEL, outline=SLATE, width=2)
        d.text((x0 + 20, y + 14), f"Stage {i + 1}  {name}", font=font(24), fill=TEXT)
        d.text((x0 + 20, y + 54), dens + (" · 일반 적 중심" if i == 0 else " · 중간 보스" if i == 1 else " · 최종 보스"), font=font(20, False), fill=MUTED)
    d.text((x0, 540), "외곽에서 중심으로 갈수록", font=font(24), fill=TEXT)
    d.text((x0, 580), "안개가 짙고 적이 강해진다", font=font(24), fill=CYAN)
    tag(img, "세계관 약도 (설계 스케치)")
    return finish(img)


def scene_room_grid():
    img = new_canvas((10, 16, 28), (20, 30, 48))
    d = ImageDraw.Draw(img)
    d.text((40, 24), "스테이지 맵 (격자형)", font=font(30), fill=TEXT)
    cols, rows = 5, 3
    cw, ch, gx, gy = 110, 80, 26, 26
    ox, oy = 50, 100
    kinds = {(0, 1): ("시작", GREEN), (1, 1): ("전투", MID), (2, 1): ("전투", MID), (2, 0): ("전투", MID),
             (3, 1): ("정비", (180, 140, 255)), (3, 2): ("고농도", WARN), (4, 1): ("보스", RED), (2, 2): ("전투", MID)}
    links = [((0, 1), (1, 1)), ((1, 1), (2, 1)), ((2, 1), (2, 0)), ((2, 1), (3, 1)), ((3, 1), (4, 1)), ((3, 1), (3, 2)), ((2, 1), (2, 2))]

    def center(c):
        return ox + c[0] * (cw + gx) + cw // 2, oy + c[1] * (ch + gy) + ch // 2
    for a, b in links:
        d.line([center(a), center(b)], fill=(120, 150, 180), width=8)
    for c, (name, col) in kinds.items():
        x0, y0 = ox + c[0] * (cw + gx), oy + c[1] * (ch + gy)
        d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=10, fill=tuple(int(v * 0.55) for v in col), outline=col, width=3)
        d.text((x0 + cw // 2, y0 + ch // 2), name, font=font(24), fill=TEXT, anchor="mm")
    cur = center((2, 1))
    d.ellipse([cur[0] - 11, cur[1] + 18, cur[0] + 11, cur[1] + 40], fill=WARN)
    d.text((cur[0] + 62, cur[1] + 30), "◀ 현재", font=font(16), fill=WARN, anchor="mm")
    d.text((50, 405), "● 방은 상하좌우로 연결 · 적을 모두 처치해야 문이 열림", font=font(21, False), fill=MUTED)
    # 단면
    px0, py0, pw, ph = 50, 450, 760, 235
    d.rounded_rectangle([px0, py0, px0 + pw, py0 + ph], radius=12, fill=(12, 18, 30), outline=SLATE, width=2)
    d.text((px0 + 16, py0 + 10), "방 한 칸의 구조 (2~3층 플랫폼)", font=font(20), fill=CYAN)
    img_rgba = img
    platform(img_rgba, px0 + 20, px0 + pw - 20, py0 + ph - 30, 20)
    platform(img_rgba, px0 + 80, px0 + 330, py0 + 140, 16)
    platform(img_rgba, px0 + 420, px0 + 690, py0 + 100, 16)
    paste_bottom(img_rgba, sprite("n09", 1), px0 + 120, py0 + 140, False)
    paste_bottom(img_rgba, sprite("enemy_slum", 1), px0 + 520, py0 + 100, False)
    d = ImageDraw.Draw(img_rgba)
    d.rectangle([px0, py0 + ph - 120, px0 + 14, py0 + ph - 30], fill=SLATE)
    d.rectangle([px0 + pw - 14, py0 + ph - 120, px0 + pw, py0 + ph - 30], fill=SLATE)
    d.rectangle([px0 + 350, py0, px0 + 410, py0 + 12], fill=SLATE)
    d.text((px0 + 380, py0 + 28), "위 출입구", font=font(14, False), fill=MUTED, anchor="mm")
    # 범례
    lx = 860
    d.text((lx, 110), "방 종류", font=font(26), fill=TEXT)
    for i, (n, col, desc) in enumerate([("시작", GREEN, "안전한 출발점"), ("전투", MID, "적을 처치하면 문이 열림"),
                                        ("정비", (180, 140, 255), "조각으로 업그레이드"), ("보스", RED, "구역 보스와 결전"), ("고농도", WARN, "게이지 +1%/2초")]):
        y = 175 + i * 68
        d.rounded_rectangle([lx, y, lx + 80, y + 54], radius=8, fill=tuple(int(v * 0.55) for v in col), outline=col, width=3)
        d.text((lx + 40, y + 27), n, font=font(22), fill=TEXT, anchor="mm")
        d.text((lx + 100, y + 27), desc, font=font(21, False), fill=MUTED, anchor="lm")
    d.text((lx, 560), "예) 전투 → 고농도 → 정비 → 보스", font=font(20, False), fill=MUTED)
    tag(img, "격자 맵 설계 목업 (실제 구현 화면 아님)")
    return finish(img)


def key(d, x, y, w, h, text, col=SLATE, tcol=TEXT, size=24):
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=tuple(int(v * 0.4) for v in col), outline=col, width=3)
    d.text((x + w / 2, y + h / 2), text, font=font(size), fill=tcol, anchor="mm")


def scene_controls():
    img = new_canvas((10, 16, 28), (18, 28, 46))
    d = ImageDraw.Draw(img)
    d.text((40, 24), "조작 방법", font=font(32), fill=TEXT)
    # 키보드
    key(d, 60, 100, 70, 70, "Q", CYAN)
    key(d, 140, 100, 70, 70, "W", GREEN)
    key(d, 220, 100, 70, 70, "E", WARN)
    key(d, 20, 180, 70, 70, "A", GREEN)
    key(d, 100, 180, 70, 70, "S", GREEN)
    key(d, 180, 180, 70, 70, "D", GREEN)
    key(d, 260, 180, 70, 70, "F", (180, 140, 255))
    key(d, 20, 260, 130, 70, "Shift", CYAN)
    key(d, 160, 260, 320, 70, "Space", GREEN)
    # 설명 목록
    legend = [("Q", "무기 교체", CYAN), ("W · Space", "점프 (공중 1회 추가)", GREEN), ("A D", "좌우 이동", GREEN),
              ("S + Space", "아래 점프 (얇은 바닥 통과)", GREEN), ("F", "상호작용 (정비방 · 문)", (180, 140, 255)),
              ("Shift", "대시 (슬롯 2개)", CYAN), ("E", "무기 강화 (게이지 -25%)", WARN)]
    for i, (k, v, col) in enumerate(legend):
        y = 112 + i * 34
        d.text((510, y), k, font=font(19), fill=col, anchor="lm")
        d.text((640, y), v, font=font(19, False), fill=TEXT, anchor="lm")
    # 마우스
    mx, my = 1010, 100
    d.rounded_rectangle([mx, my, mx + 160, my + 240], radius=80, fill=(30, 42, 64), outline=SLATE, width=4)
    d.pieslice([mx, my, mx + 160, my + 160], 180, 270, fill=(30, 100, 140), outline=SLATE)
    d.pieslice([mx, my, mx + 160, my + 160], 270, 360, fill=(120, 60, 50), outline=SLATE)
    d.text((mx + 40, my + 50), "L", font=font(30), fill=TEXT, anchor="mm")
    d.text((mx + 120, my + 50), "R", font=font(30), fill=TEXT, anchor="mm")
    d.text((mx + 80, my + 266), "좌클릭: 공격 · 조준", font=font(19), fill=TEXT, anchor="mm")
    d.text((mx + 80, my + 296), "우클릭: 대시", font=font(19), fill=TEXT, anchor="mm")
    # 이동 궤적
    platform(img, 40, 1240, 650, 40)
    paste_bottom(img, sprite("n09", 2), 80, 650, False)
    pts = [(130, 575), (210, 500), (280, 455), (350, 500), (420, 440), (490, 410)]
    d.line(pts, fill=GREEN, width=5)
    for p in (pts[2], pts[4]):
        d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=GREEN)
    d.text((330, 408), "1단 점프 → 2단 점프", font=font(22), fill=GREEN, anchor="mm")
    arrow(d, 620, 600, 900, 540, CYAN, 8, 28)
    d.text((760, 500), "대시 (마우스 방향)", font=font(22), fill=CYAN, anchor="mm")
    crosshair(img, 980, 520, TEXT)
    glow(img, 760, 585, 140, 30, CYAN, 80, 20)
    tag(img, "조작 설명도 (설계 스케치)")
    return finish(img)


def scene_gauge():
    img = new_canvas((10, 16, 28), (18, 28, 46))
    d = ImageDraw.Draw(img)
    d.text((40, 24), "헤이즈 게이지: 구간별 상태", font=font(32), fill=TEXT)
    draw_gauge(img, 80, 130, 1120, 44, 62, True, True)
    states = [("페이드 1~19%", RED, "이동 -20% · 공격력 ×0.8", "0%가 되면 사망", 10, False, None),
              ("각성 50~89%", CYAN, "공격력 ×1.5", "속도 +25%", 62, True, None),
              ("위험 90~99%", WARN, "공격력 ×1.8", "속도 +35% · 경고", 94, True, RED)]
    for i, (name, col, l1, l2, val, aura, vig) in enumerate(states):
        x0 = 60 + i * 400
        card = Image.new("RGBA", (360, 400), PANEL + (255,))
        cd = ImageDraw.Draw(card)
        cd.rectangle([0, 0, 359, 399], outline=col, width=3)
        if aura:
            glow(card, 180, 220, 90 if col == CYAN else 100, 140, col, 110, 30)
        if vig:
            vignette(card, RED, 170)
        spr = sprite("n09", 3)
        if val < 20:
            spr = spr.convert("LA").convert("RGBA")
        card.alpha_composite(spr, (180 - spr.width // 2, 360 - spr.height))
        cd = ImageDraw.Draw(card)
        cd.text((180, 28), name, font=font(26), fill=col, anchor="mm")
        cd.text((180, 62), f"{l1} · {l2}" if False else l1, font=font(20), fill=TEXT, anchor="mm")
        cd.text((180, 88), l2, font=font(20), fill=TEXT, anchor="mm")
        img.alpha_composite(card, (x0, 260))
    tag(img, "구간별 표현 설계 목업 (실제 구현 화면 아님)")
    return finish(img)


def battle_panel(gauge, enhanced, enemies_close):
    img = new_canvas()
    bg_pillars(img, 8)
    fog(img, 8, (60, 120, 160), 36, 4, 0.5)
    platform(img, 0, 640, 560, 80)
    paste_bottom(img, sprite("n09", 3), 120, 560)
    paste_bottom(img, sprite("enemy_guard", 3), 340 if enemies_close else 430, 560, True)
    paste_bottom(img, sprite("enemy_hound", 2), 470, 560, True)
    if enhanced:
        glow(img, 210, 440, 110, 160, CYAN, 120, 30)
        slash_arc(img, 260, 440, 120, 320, 60, CYAN, 16)
        dmg(img, 400, 330, "-45", CYAN, 34)
    else:
        dmg(img, 400, 330, "-36", WARN, 30)
    if gauge >= 90:
        vignette(img, RED, 170)
    d = ImageDraw.Draw(img)
    draw_gauge(img, 40, 70, 560, 16, gauge, False)
    name, col = zone_of(gauge)
    d.text((40, 20), f"게이지 {gauge}%  {name}", font=font(24), fill=col)
    return img


def scene_combat_example():
    img = Image.new("RGBA", (W, H), NAVY + (255,))
    left = battle_panel(92, False, True).resize((600, 338))
    right = battle_panel(67, True, False).resize((600, 338))
    img.alpha_composite(left.convert("RGBA"), (20, 150))
    img.alpha_composite(right.convert("RGBA"), (660, 150))
    d = ImageDraw.Draw(img)
    d.text((320, 110), "① 위험 구간 진입", font=font(30), fill=WARN, anchor="mm")
    d.text((960, 110), "③ 각성 복귀 + 무기 강화", font=font(30), fill=CYAN, anchor="mm")
    arrow(d, 626, 320, 654, 320, TEXT, 6, 18)
    d.rounded_rectangle([360, 540, 920, 660], radius=14, fill=PANEL, outline=CYAN, width=3)
    d.text((640, 585), "② E 키: 게이지 92% → 67%", font=font(28), fill=CYAN, anchor="mm")
    d.text((640, 630), "장착 무기 8초 강화 · 폭발 회피", font=font(20, False), fill=TEXT, anchor="mm")
    d.text((220, 520), "대미지 36 (기본 20 × 1.8)", font=font(22, False), fill=MUTED, anchor="mm")
    d.text((1060, 520), "대미지 45 (20 × 1.5 × E 1.5)", font=font(22, False), fill=CYAN, anchor="mm")
    d.text((640, 40), "전투 예시: 게이지를 써서 폭발을 피한다", font=font(34), fill=TEXT, anchor="mm")
    tag(img, "상황 설명 목업 (실제 구현 화면 아님)")
    return finish(img)


def stage_panel(kind):
    img = Image.new("RGBA", (400, 360))
    d = ImageDraw.Draw(img)
    tops = {"slum": ((26, 30, 34), (52, 56, 60)), "factory": ((34, 24, 20), (70, 46, 34)), "tower": ((8, 14, 30), (20, 40, 70))}[kind]
    for y in range(360):
        t = y / 360
        d.line([(0, y), (400, y)], fill=tuple(int(tops[0][i] + (tops[1][i] - tops[0][i]) * t) for i in range(3)) + (255,))
    rnd = random.Random(7)
    if kind == "slum":
        for x in range(10, 400, 70):
            h = rnd.randint(90, 200)
            d.rectangle([x, 300 - h, x + 50, 300], fill=(22, 26, 30))
            for wy in range(300 - h + 14, 280, 34):
                if rnd.random() < 0.3:
                    d.rectangle([x + 16, wy, x + 32, wy + 14], fill=(60, 90, 100))
    elif kind == "factory":
        d.rectangle([0, 80, 400, 100], fill=(60, 40, 30))
        for x in range(30, 400, 90):
            d.rectangle([x, 100, x + 14, 300], fill=(54, 38, 30))
            d.ellipse([x - 20, 60, x + 34, 120], outline=(92, 60, 40), width=6)
    else:
        d.polygon([(150, 300), (250, 300), (240, 60), (160, 60)], fill=(10, 16, 28))
        for y in range(80, 290, 40):
            d.rectangle([190, y, 210, y + 16], fill=(60, 140, 190))
    fog(img, 6, (80, 140, 180), 36, 5, 0.5)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 300, 400, 360], fill=(34, 46, 68))
    d.rectangle([0, 300, 400, 305], fill=(80, 110, 140))
    return img


def scene_stages():
    img = new_canvas((10, 16, 28), (18, 28, 46))
    d = ImageDraw.Draw(img)
    d.text((40, 20), "3개 구역 · 6종의 적", font=font(32), fill=TEXT)
    data = [("slum", "Stage 1 슬럼", [("enemy_slum", 1.6), ("enemy_thrower", 1.6)]),
            ("factory", "Stage 2 철골 공장", [("enemy_guard", 1.6), ("boss_crasher", 1.1)]),
            ("tower", "Stage 3 감시자의 탑", [("enemy_hound", 1.6), ("boss_ark", 1.5)])]
    for i, (kind, name, mobs) in enumerate(data):
        x0 = 40 + i * 410
        panel = stage_panel(kind)
        x = 20
        for n, sc in mobs:
            s = sprite(n, 1)
            s = s.resize((int(s.width * sc), int(s.height * sc)), Image.NEAREST)
            panel.alpha_composite(s, (x, 300 - s.height))
            x += s.width + 24
        img.alpha_composite(panel, (x0, 100))
        d = ImageDraw.Draw(img)
        d.rectangle([x0, 100, x0 + 400, 460], outline=SLATE, width=3)
        d.text((x0 + 200, 490), name, font=font(26), fill=CYAN, anchor="mm")
    d.text((640, 560), "일반 적 4종 + 보스 2종", font=font(28), fill=TEXT, anchor="mm")
    d.text((640, 606), "슬럼 폐인 · 고철 투척병 · 안개 사냥개 · 중장갑 간수 / 크래셔 · 아크", font=font(22, False), fill=MUTED, anchor="mm")
    tag(img, "스테이지별 구성 설계 목업 (실제 구현 화면 아님)")
    return finish(img)


def scene_gantt():
    img = new_canvas((10, 16, 28), (18, 28, 46))
    d = ImageDraw.Draw(img)
    d.text((40, 20), "개발 일정 (11/5 ~ 12/14)", font=font(32), fill=TEXT)
    rows = [("1주  11/5~11/11", "프레임워크 · 이동 · 2단 점프 · 충돌", 0, 1, CYAN),
            ("2주  11/12~11/18", "마우스 전투 · 대시 슬롯 · 몹 2종 · 게이지 기본형", 1, 2, CYAN),
            ("3주  11/19~11/25", "게이지 구간 효과 · E 강화 · 격자 맵 · 정비방", 2, 3, CYAN),
            ("4주  11/26~12/2", "몹·무기 확장 · Stage 2 · 중간 보스 · 효과음", 3, 4, CYAN),
            ("5주  12/3~12/9", "최종 보스 · BGM · 이펙트 · 밸런싱", 4, 5, CYAN),
            ("완충  12/10~12/14", "버그 수정 · 최종 제출", 5, 5.7, WARN)]
    tx0, tx1 = 980, 1240
    unit = (tx1 - tx0) / 5.7
    for i, (wk, desc, a, b, col) in enumerate(rows):
        y = 95 + i * 84
        d.rounded_rectangle([30, y, 1250, y + 70], radius=12, fill=PANEL, outline=SLATE, width=2)
        d.text((50, y + 35), wk, font=font(22), fill=col, anchor="lm")
        d.text((290, y + 35), desc, font=font(22, False), fill=TEXT, anchor="lm")
        d.rectangle([tx0, y + 28, tx1, y + 42], fill=(34, 46, 68))
        d.rectangle([tx0 + a * unit, y + 24, tx0 + b * unit - 3, y + 46], fill=col)
    d.text((40, 620), "핵심 재미인 게이지를 2~3주차에 먼저 완성해 밸런싱 시간을 확보한다", font=font(24), fill=CYAN)
    d.text((40, 662), "지연되면 Stage 2·중간 보스 → 무기 일부 → 부가 효과 순으로 줄인다", font=font(22, False), fill=MUTED)
    return finish(img)


def scene_credits():
    img = new_canvas((8, 12, 22), (16, 24, 40))
    d = ImageDraw.Draw(img)
    d.text((W // 2, 50), "CREDITS", font=font(40), fill=TEXT, anchor="mm")
    cols = [("[ 외부 에셋 ]", CYAN, ["타일 · UI · 효과음", "CC0 · CC-BY 등 무료", "제작자·URL·라이선스"]),
            ("[ AI 생성 ]", WARN, ["캐릭터 · 적 · 보스 이미지", "사용 도구 · 생성일 표기", "프롬프트는 문서에 기록"]),
            ("[ 직접 제작 ]", GREEN, ["게임 기획 · 규칙 · 수치", "pico2d 코드 · 밸런싱", "화면 설계 목업"])]
    for i, (head, col, lines) in enumerate(cols):
        x0 = 60 + i * 400
        d.rounded_rectangle([x0, 120, x0 + 360, 470], radius=14, fill=PANEL, outline=col, width=3)
        d.text((x0 + 180, 160), head, font=font(28), fill=col, anchor="mm")
        for j, ln in enumerate(lines):
            d.text((x0 + 24, 230 + j * 70), "• " + ln, font=font(21, False), fill=TEXT)
    x = 200
    for n, k in (("n09", 2), ("enemy_slum", 2), ("enemy_thrower", 2), ("enemy_hound", 2), ("enemy_guard", 2), ("boss_crasher", 1), ("boss_ark", 2)):
        s = sprite(n, k)
        paste_bottom(img, s, x, 660, False)
        x += s.width + 40
    tag(img, "엔딩 크레딧 설계 목업")
    return finish(img)


# ---------------------------------------------------------------- 기획서 PPT 추가 목업
def scene_weapons():
    img = new_canvas((10, 16, 28), (18, 28, 46))
    d = ImageDraw.Draw(img)
    d.text((40, 20), "무기 4종: 구간 변화와 E 강화", font=font(30), fill=TEXT)
    cards = [("철파이프", "충전형", ["노멀 3연타 +6%", "각성 범위 +30%", "위험 4연타 연쇄"], "E: 전방 안개 참격"),
             ("식칼 묶음", "구간 연동형", ["노멀 2발", "각성 3발 부채꼴", "위험 3발 관통"], "E: 발사 +2, 관통"),
             ("헤이즈 건틀릿", "소모형", ["노멀 충전 1.2초", "각성 0.8초 ×1.3", "위험 즉발 -15%"], "E: 충전 절반 ×1.5"),
             ("헤이즈 사슬", "제어형", ["노멀 1마리", "각성 2마리 · 사거리", "위험 기절 1초"], "E: 기절, 다수 관통")]
    zcols = [MID, CYAN, WARN]
    for i, (n, t, zl, e) in enumerate(cards):
        x0 = 30 + i * 310
        d.rounded_rectangle([x0, 80, x0 + 290, 650], radius=14, fill=PANEL, outline=SLATE, width=2)
        d.text((x0 + 145, 112), n, font=font(26), fill=CYAN, anchor="mm")
        d.text((x0 + 145, 148), t, font=font(18), fill=MUTED, anchor="mm")
        ex = Image.new("RGBA", (260, 200), (14, 20, 32, 255))
        ed = ImageDraw.Draw(ex)
        ed.rectangle([0, 170, 260, 200], fill=(34, 46, 68))
        sp = sprite("n09", 2)
        ex.alpha_composite(sp, (20, 170 - sp.height))
        if i == 0:
            slash_arc(ex, 90, 100, 70, 300, 60, CYAN, 10)
            ed.rectangle([150, 90, 240, 102], fill=(79, 195, 247, 120))
        elif i == 1:
            for ang in (-20, 0, 20):
                ed.line([(90, 100), (240, 100 + ang * 1.6)], fill=CYAN, width=4)
        elif i == 2:
            ed.ellipse([100, 60, 180, 140], outline=CYAN, width=5)
            ed.ellipse([130, 90, 210, 170], outline=(79, 195, 247, 130), width=3)
        else:
            ed.line([(90, 110), (210, 130)], fill=SLATE, width=6)
            sl = sprite("enemy_slum", 1)
            ex.alpha_composite(sl, (200, 170 - sl.height))
            arrow(ed, 205, 140, 140, 125, CYAN, 4, 12)
        img.alpha_composite(ex, (x0 + 15, 175))
        d = ImageDraw.Draw(img)
        for j, ln in enumerate(zl):
            d.text((x0 + 18, 410 + j * 40), ln, font=font(17), fill=zcols[j])
        d.rounded_rectangle([x0 + 14, 560, x0 + 276, 628], radius=10, fill=(20, 44, 64), outline=CYAN, width=2)
        d.text((x0 + 145, 594), e, font=font(18), fill=CYAN, anchor="mm")
    tag(img, "무기 효과 설명도 (설계 스케치)")
    return finish(img)

def scene_boss_crasher():
    img = new_canvas((24, 16, 12), (50, 34, 26))
    d = ImageDraw.Draw(img)
    platform(img, 0, W, 600, 120)
    paste_bottom(img, sprite("n09", 3), 100, 600)
    paste_bottom(img, sprite("boss_crasher", 3), 700, 600, True)
    arrow(d, 640, 470, 360, 470, WARN, 10, 34)
    d.text((500, 430), "돌진", font=font(28), fill=WARN, anchor="mm")
    for r in (60, 110, 160):
        d.arc([980 - r, 590 - r // 3, 980 + r, 590 + r // 3], 180, 360, fill=RED, width=6)
    d.text((700, 655), "바닥 찍기 충격파: 게이지 -20%", font=font(22), fill=RED, anchor="mm")
    glow(img, 1020, 300, 70, 50, CYAN, 110, 24)
    glow(img, 860, 280, 60, 40, CYAN, 90, 24)
    d = ImageDraw.Draw(img)
    d.text((960, 215), "증기 분출: 게이지 +12%", font=font(22), fill=CYAN, anchor="mm")
    d.text((40, 120), "중간 보스 크래셔 (Stage 2)", font=font(32), fill=TEXT)
    d.text((40, 166), "돌진(피해만) · 충격파 -20% · 증기 분출 +12%", font=font(22, False), fill=MUTED)
    hud(img, 38, 0.7, 2, 2, ("건틀릿", "파이프"), 0)
    tag(img, "보스 패턴 설명도 (설계 스케치)")
    return finish(img)


def scene_boss_ark():
    img = new_canvas((8, 14, 30), (20, 40, 70))
    d = ImageDraw.Draw(img)
    platform(img, 0, W, 610, 110)
    paste_bottom(img, sprite("n09", 3), 120, 610)
    paste_bottom(img, sprite("boss_ark", 4), 860, 610, True)
    for i in range(5):
        y = 250 + i * 55
        d.line([(850, 340), (380, y)], fill=(79, 195, 247), width=3)
    d.text((560, 262), "헤이즈 탄막: 1발당 +5%", font=font(22), fill=CYAN, anchor="mm")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([180, 580, 560, 640], fill=(255, 90, 90, 90))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    d.text((370, 660), "오염 장판: 위에서 초당 +5%", font=font(22), fill=RED, anchor="mm")
    for r, col in ((120, WARN), (165, RED)):
        d.ellipse([990 - r, 400 - r, 990 + r, 400 + r], outline=col, width=4)
    d.text((690, 205), "흡수 파동: -25%", font=font(21), fill=WARN, anchor="mm")
    d.text((690, 240), "과충전 파동: +25%", font=font(21), fill=RED, anchor="mm")
    d.text((40, 120), "최종 보스 아크 (Stage 3)", font=font(32), fill=TEXT)
    d.text((40, 166), "탄막 · 베기 -10% · 두 파동 · 장판 (3페이즈)", font=font(22, False), fill=MUTED)
    hud(img, 74, 0.6, 3, 3, ("건틀릿", "식칼"), 0, True)
    tag(img, "보스 패턴 설명도 (설계 스케치)")
    return finish(img)


def scene_gauge_graph():
    img = new_canvas((10, 16, 28), (18, 28, 46))
    d = ImageDraw.Draw(img)
    d.text((40, 20), "게이지의 흐름 (플레이 시나리오)", font=font(30), fill=TEXT)
    gx0, gy0, gx1, gy1 = 130, 100, 1220, 540
    for lo, hi, col, name in ((0, 19, DEATH, "페이드"), (20, 49, MID, "노멀"), (50, 89, CYAN, "각성"), (90, 99, WARN, "위험")):
        y0 = gy1 - (gy1 - gy0) * (hi + 1) / 100
        y1 = gy1 - (gy1 - gy0) * lo / 100
        d.rectangle([gx0, y0, gx1, y1], fill=tuple(int(v * 0.25) for v in col))
        d.text((gx0 - 10, (y0 + y1) / 2), name, font=font(17), fill=col, anchor="rm")
    d.rectangle([gx0, gy0 - 8, gx1, gy0 + 4], fill=tuple(int(v * 0.5) for v in RED))
    d.text((gx1 - 6, gy1 - 8), "0% = 사망", font=font(17), fill=RED, anchor="rd")
    pts = [(0, 30), (0.7, 15), (1.5, 58), (2.5, 92), (2.9, 67), (3.9, 100), (4.0, 30), (4.7, 22)]
    xs = lambda t: gx0 + (gx1 - gx0) * t / 4.9
    ys = lambda v: gy1 - (gy1 - gy0) * v / 100
    d.line([(xs(t), ys(v)) for t, v in pts], fill=TEXT, width=6)
    notes = [(0, 30, "방 진입 30%", 95, -30), (0.7, 15, "시간 경과 15% 페이드", 40, 30), (1.5, 58, "연속 타격 58%", -70, -40),
             (2.5, 92, "위험 92%", -10, -40), (2.9, 67, "E 강화 67%", 60, 38), (3.9, 100, "100% 폭발", -10, -42),
             (4.0, 30, "초기화 30%", 60, 34), (4.7, 22, "22%", 0, 28)]
    for t, v, txt, dx, dy in notes:
        col = WARN if v >= 90 else (RED if v < 20 else CYAN)
        d.ellipse([xs(t) - 10, ys(v) - 10, xs(t) + 10, ys(v) + 10], fill=col, outline=TEXT, width=3)
        d.text((xs(t) + dx, ys(v) + dy), txt, font=font(19), fill=TEXT, anchor="mm")
    d.text((640, 585), "시간 →", font=font(20, False), fill=MUTED, anchor="mm")
    d.text((640, 640), "시간이 지나면 내려가고(0%는 사망), 싸우면 올라간다(100% 폭발).", font=font(22), fill=CYAN, anchor="mm")
    tag(img, "")
    return finish(img)

def scene_upgrades():
    img = new_canvas((10, 16, 28), (18, 28, 46))
    d = ImageDraw.Draw(img)
    d.text((40, 20), "정비방 업그레이드 7종 (각 3단계)", font=font(32), fill=TEXT)
    items = [("게이지 용량", "한계 100→120→140→160%"), ("흡수 효율", "처치 +8→10→12→14%"),
             ("결핍 방지", "감소 간격 3→4→5→6초"), ("강화 효율", "E 소모 25→20→17→15%"),
             ("오버로드 내성", "폭발 피해 20→15→10→5%"), ("대시 강화", "슬롯 2→3→4→5개"),
             ("기본 성장", "공격력 / 최대 체력")]
    for i, (n, e) in enumerate(items):
        col, row = i % 2, i // 2
        x0, y0 = 40 + col * 610, 100 + row * 135
        d.rounded_rectangle([x0, y0, x0 + 580, y0 + 115], radius=14, fill=PANEL, outline=CYAN if i in (0, 5) else SLATE, width=3 if i in (0, 5) else 2)
        d.text((x0 + 24, y0 + 30), n, font=font(26), fill=CYAN, anchor="lm")
        d.text((x0 + 24, y0 + 80), e, font=font(22, False), fill=TEXT, anchor="lm")
        for s in range(3):
            d.rectangle([x0 + 470 + s * 34, y0 + 20, x0 + 496 + s * 34, y0 + 46], fill=CYAN if s == 0 else (40, 52, 74), outline=TEXT)
    d.text((660, 640), "헤이즈 조각(재화)으로 구매 · 게이지와는 별개", font=font(24), fill=MUTED)
    tag(img, "")
    return finish(img)


SCENES = {
    "slide_01": scene_title, "slide_02": scene_battle, "slide_03": scene_world_map,
    "slide_04": scene_room_grid, "slide_05": scene_controls, "slide_06": scene_gauge,
    "slide_07": scene_combat_example, "slide_08": scene_stages, "slide_09": scene_gantt,
    "slide_10": scene_credits,
    "mock_weapons": scene_weapons, "mock_boss_crasher": scene_boss_crasher,
    "mock_boss_ark": scene_boss_ark, "mock_gauge_graph": scene_gauge_graph,
    "mock_upgrades": scene_upgrades,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in SCENES.items():
        fn().save(os.path.join(OUT, f"{name}.png"))
        print("saved", name)


if __name__ == "__main__":
    main()
