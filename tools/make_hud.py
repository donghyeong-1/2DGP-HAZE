"""HUD 그림 조각을 코드로 그린다 (이미지 모델 없음, Pillow). code-drawn, 자체 제작.

게이지 양끝 장식, 게이지 표시 바늘, 대시 결정 칸, 콤보 칸, 조준점, 미니맵 방 종류 아이콘, 체력 아이콘, E 키 표시.
틀(테두리)은 크기가 변하므로 게임에서 사각형으로 그리고(src/ui.py의 _frame), 여기서는 모양이 있는 조각만 만든다.
규칙(docs/pixel_rules.md): 도트 1px, 알파는 0 또는 255, 외곽선 #0b1020. 색만으로 뜻을 전하지 않도록
(game-ui-ux 지침) 방 종류와 상태를 모양으로도 구분한다.

결과: assets/ui/hud_*.png
사용: python tools/make_hud.py
"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'ui')

K = (11, 16, 32, 255)          # 외곽선
D = (26, 34, 56, 255)
B = (42, 53, 82, 255)
M = (58, 74, 108, 255)
L = (86, 108, 150, 255)
H = (155, 178, 214, 255)
C_DEEP = (22, 74, 102, 255)    # 청록 계열 (헤이즈)
C_DARK = (31, 106, 138, 255)
C_MID = (63, 177, 207, 255)
C_LIGHT = (166, 236, 251, 255)
C_CORE = (234, 255, 255, 255)
GOLD = (242, 210, 116, 255)
GOLD_D = (170, 136, 48, 255)
RED = (226, 100, 110, 255)
RED_D = (142, 46, 66, 255)
ORANGE = (240, 150, 60, 255)
WHITE = (235, 240, 250, 255)
GRAY = (70, 80, 100, 255)
CLEAR = (0, 0, 0, 0)


def canvas(w, h):
    img = Image.new('RGBA', (w, h), CLEAR)
    return img, ImageDraw.Draw(img)


def save(img, name):
    img.save(os.path.join(OUT, f'hud_{name}.png'))
    print('saved hud_' + name, img.size)


def crystal(d, pts, body, light, dark):
    """각진 결정: 몸통, 왼쪽 위 밝은 면, 오른쪽 아래 어두운 면, 외곽선."""
    d.polygon(pts, fill=body, outline=K)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = sum(xs) // len(xs), sum(ys) // len(ys)
    top = min(pts, key=lambda p: p[1])
    left = min(pts, key=lambda p: p[0])
    right = max(pts, key=lambda p: p[0])
    bottom = max(pts, key=lambda p: p[1])
    d.polygon([(top[0], top[1] + 2), (left[0] + 2, left[1]), (cx, cy)], fill=light)
    d.polygon([(right[0] - 2, right[1]), (bottom[0], bottom[1] - 2), (cx, cy)], fill=dark)
    d.line([top, (cx, cy)], fill=C_CORE if light == C_LIGHT else light)
    d.polygon(pts, outline=K)


def gauge_caps():
    """게이지 양끝 장식: 강철 받침에 박힌 헤이즈 결정 (왼쪽 것을 만들고 오른쪽은 좌우 반전)."""
    w, h = 40, 64
    img, d = canvas(w, h)
    d.polygon([(10, 8), (w - 1, 8), (w - 1, h - 9), (10, h - 9), (2, h // 2)], fill=M, outline=K)
    d.line([(11, 9), (w - 2, 9)], fill=H)
    d.line([(11, h - 10), (w - 2, h - 10)], fill=D)
    d.line([(4, h // 2), (11, 10)], fill=L)
    crystal(d, [(20, 14), (30, 32), (20, 50), (10, 32)], C_MID, C_LIGHT, C_DARK)
    for y in (13, h - 14):
        d.rectangle([33, y - 1, 35, y + 1], fill=D)
        d.point((33, y - 1), fill=H)
    save(img, 'gauge_cap_l')
    save(img.transpose(Image.FLIP_LEFT_RIGHT), 'gauge_cap_r')


def marker():
    """게이지 현재 값 바늘: 위아래 삼각 머리와 가는 흰 줄."""
    w, h = 24, 72
    img, d = canvas(w, h)
    d.rectangle([9, 10, 14, h - 11], fill=K)
    d.rectangle([10, 10, 13, h - 11], fill=WHITE)
    d.polygon([(2, 0), (21, 0), (12, 12), (11, 12)], fill=WHITE, outline=K)
    d.polygon([(2, h - 1), (21, h - 1), (12, h - 13), (11, h - 13)], fill=WHITE, outline=K)
    d.line([(5, 2), (18, 2)], fill=C_LIGHT)
    save(img, 'marker')


def dash_pips():
    """대시 칸: 비스듬한 결정. 찬 칸은 청록, 빈 칸은 어두운 틀만 (모양은 같고 속이 비어 보인다)."""
    w, h = 54, 34
    pts = [(10, 1), (w - 2, 1), (w - 11, h - 2), (1, h - 2)]
    img, d = canvas(w, h)
    d.polygon(pts, fill=C_MID, outline=K)
    d.polygon([(12, 3), (w - 6, 3), (w - 9, 9), (9, 9)], fill=C_LIGHT)
    d.polygon([(6, h - 9), (w - 12, h - 9), (w - 14, h - 4), (4, h - 4)], fill=C_DARK)
    d.line([(14, 5), (30, 5)], fill=C_CORE)
    d.polygon(pts, outline=K)
    save(img, 'dash_on')
    img, d = canvas(w, h)
    d.polygon(pts, fill=D, outline=K)
    d.polygon([(12, 3), (w - 6, 3), (w - 7, 5), (11, 5)], fill=B)
    d.line([(8, h - 5), (w - 14, h - 5)], fill=M)
    d.polygon(pts, outline=K)
    save(img, 'dash_off')


def combo_pips():
    """콤보 칸: 꺼짐(빈 틀), 켜짐(흰 쐐기), 마무리(주황 불꽃 쐐기). 3타째는 모양도 다르다(톱니)."""
    w, h = 46, 44
    base = [(1, 6), (w - 8, 1), (w - 2, h - 7), (7, h - 2)]
    for name, fill, light, dark in (('off', D, B, D), ('on', WHITE, C_CORE, H), ('fin', ORANGE, GOLD, RED_D)):
        img, d = canvas(w, h)
        d.polygon(base, fill=fill, outline=K)
        d.polygon([(4, 8), (w - 10, 4), (w - 9, 9), (6, 13)], fill=light)
        d.polygon([(9, h - 10), (w - 6, h - 13), (w - 5, h - 9), (9, h - 5)], fill=dark)
        if name == 'fin':
            for x in (12, 22, 32):                           # 마무리 칸은 위에 톱니
                d.polygon([(x, 8), (x + 4, 0), (x + 8, 8)], fill=GOLD, outline=K)
        d.polygon(base, outline=K)
        save(img, 'combo_' + name)


def reticle():
    """조준점: 가운데 점과 네 팔. 공격 준비가 안 됐으면 팔이 벌어지고 회색이다."""
    for name, color, gap in (('ready', WHITE, 7), ('wait', GRAY, 12)):
        s = 56
        img, d = canvas(s, s)
        c = s // 2
        arms = [(c - gap - 14, c - 2, c - gap, c + 1), (c + gap, c - 2, c + gap + 14, c + 1),
                (c - 2, c - gap - 14, c + 1, c - gap), (c - 2, c + gap, c + 1, c + gap + 14)]
        for x0, y0, x1, y1 in arms:
            d.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], fill=K)
        for x0, y0, x1, y1 in arms:
            d.rectangle([x0, y0, x1, y1], fill=color)
        d.rectangle([c - 3, c - 3, c + 2, c + 2], fill=K)
        d.rectangle([c - 2, c - 2, c + 1, c + 1], fill=C_LIGHT if name == 'ready' else color)
        save(img, 'reticle_' + name)


def map_icons():
    """미니맵 방 종류 아이콘 (20x16): 황금방 별, 보스 뿔 달린 머리, 정비방 렌치, 고농도 물방울."""
    w, h = 20, 16
    img, d = canvas(w, h)                                     # 황금방: 마름모 별
    d.polygon([(10, 0), (13, 5), (19, 8), (13, 10), (10, 15), (7, 10), (1, 8), (7, 5)], fill=GOLD, outline=K)
    d.point((10, 7), fill=WHITE)
    save(img, 'map_gold')
    img, d = canvas(w, h)                                     # 보스: 뿔 + 얼굴 + 눈
    d.polygon([(2, 0), (6, 5), (14, 5), (18, 0), (16, 9), (13, 15), (7, 15), (4, 9)], fill=RED, outline=K)
    d.rectangle([6, 8, 8, 10], fill=K)
    d.rectangle([12, 8, 14, 10], fill=K)
    save(img, 'map_boss')
    img, d = canvas(w, h)                                     # 정비방: 렌치
    d.rectangle([8, 5, 11, 15], fill=C_LIGHT, outline=K)
    d.polygon([(4, 0), (8, 3), (12, 3), (16, 0), (16, 6), (12, 8), (8, 8), (4, 6)], fill=C_LIGHT, outline=K)
    d.rectangle([9, 0, 11, 3], fill=CLEAR)
    save(img, 'map_shop')
    img, d = canvas(w, h)                                     # 고농도: 물방울
    d.polygon([(10, 0), (16, 9), (14, 14), (6, 14), (4, 9)], fill=ORANGE, outline=K)
    d.point((8, 10), fill=GOLD)
    save(img, 'map_haze')


def heart():
    img, d = canvas(30, 28)
    d.polygon([(7, 1), (14, 6), (15, 6), (22, 1), (28, 7), (28, 13), (15, 26), (14, 26), (1, 13), (1, 7)], fill=RED, outline=K)
    d.polygon([(7, 3), (11, 6), (6, 11), (3, 8)], fill=(255, 170, 170, 255))
    d.polygon([(22, 16), (26, 12), (26, 14), (16, 24)], fill=RED_D)
    save(img, 'heart')


def key_e():
    """E 키 표시 (키캡 모양에 E를 직접 그린다)."""
    s = 40
    img, d = canvas(s, s)
    d.rectangle([1, 1, s - 2, s - 2], fill=M, outline=K)
    d.rectangle([3, 3, s - 4, s - 8], fill=H)
    d.rectangle([3, s - 7, s - 4, s - 4], fill=D)
    d.rectangle([4, 4, s - 5, 5], fill=C_CORE)
    for box in ([13, 9, 16, 27], [13, 9, 26, 12], [13, 17, 23, 20], [13, 24, 26, 27]):
        d.rectangle(box, fill=K)
    for x, y in ((1, 1), (s - 2, 1), (1, s - 2), (s - 2, s - 2)):
        d.point((x, y), fill=CLEAR)
    save(img, 'key_e')


def main():
    os.makedirs(OUT, exist_ok=True)
    for fn in (gauge_caps, marker, dash_pips, combo_pips, reticle, map_icons, heart, key_e):
        fn()


if __name__ == '__main__':
    main()
