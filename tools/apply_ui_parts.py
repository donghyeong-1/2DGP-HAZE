"""Gemini G06 UI 부품 시트(C안 결정형)를 게임 그림으로 굽는다 (2026-11-25).

원본: assets/sprites/gemini/ui_parts_v1/c_frames.png·c_bars.png·c_icons.png·c_cards.png
      (마젠타 바탕, 13색, 목표 크기의 8배. docs/gemini/tasks/G06_ui_parts.md, 보고서 docs/gemini/reports/G06.md)
결과: assets/ui/uc_*.png (960x540 격자의 1점 = 화면 2px. 캐릭터와 같은 도트 크기)

1. 시트를 1/8로 줄이고(최근접) 부품을 잘라 마젠타를 투명으로 바꾼다. 색은 시트의 13색 그대로.
2. 그대로 쓰는 부품(아이콘·첨탑·바늘·카드 테두리·9칸 판)은 2배로 키워 쓴다.
3. 게임 쪽 크기에 맞춰야 하는 부품은 시트의 줄 구성을 그대로 따라 다시 짠다(늘이지 않고 가운데 줄을 반복):
   게이지 몸통(속 높이 20px), 체력 막대 틀(속 24px, 오른쪽 끝 사선), 보스 막대 끝 결정, 막대 속 무늬(색 10가지 x 높이 5가지),
   얇은 막대 틀, 꺼진 키캡. 무엇을 어떻게 바꿨는지는 아래 함수마다 적었다.

실행: python tools/apply_ui_parts.py
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'sprites', 'gemini', 'ui_parts_v1')
DST = os.path.join(ROOT, 'assets', 'ui')
SCALE = 2

# G06 팔레트
N1, N2, N3 = (13, 18, 31), (22, 30, 49), (34, 44, 69)
WHITE, GREY = (242, 246, 250), (140, 152, 176)
C_HI, C_MID, C_LO = (159, 247, 238), (46, 230, 214), (11, 106, 116)
RED, RED_LO, ORANGE = (224, 64, 76), (138, 31, 44), (255, 154, 60)
GOLD, GOLD_LO = (255, 211, 110), (154, 106, 28)

_sheets = {}


def sheet(name):
    if name not in _sheets:
        im = Image.open(os.path.join(SRC, f'c_{name}.png')).convert('RGB')
        im = im.resize((im.width // 8, im.height // 8), Image.NEAREST)
        rgb = np.array(im)
        a = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])
        a[(rgb[:, :, 0] == 255) & (rgb[:, :, 1] == 0) & (rgb[:, :, 2] == 255)] = 0
        _sheets[name] = a
    return _sheets[name]


def part(name, x, y, w, h):
    return sheet(name)[y:y + h, x:x + w].copy()


def save(a, name):
    im = Image.fromarray(np.ascontiguousarray(a), 'RGBA')
    im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST).save(os.path.join(DST, f'uc_{name}.png'))


def rows(spec, width):
    """[(색, 줄 수)]를 위에서부터 쌓은 width 폭 그림."""
    out = []
    for color, n in spec:
        px = (0, 0, 0, 0) if color is None else (*color, 255)
        out += [[px] * width] * n
    return np.array(out, np.uint8)


def mix(a, b, k):
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))


# ----- 그대로 쓰는 부품: (시트, x, y, w, h) -----
PARTS = {
    # 판 (hud_kit.KITS: 9칸으로 나눠 그린다)
    'kit_panel': ('frames', 14, 6, 48, 48),          # 큰 판: 일시정지 '조작'·'이번 판', 아이템 띠
    'kit_plate': ('frames', 133, 18, 24, 24),        # 작은 HUD 틀: 미니맵, 칩, 아이템 칸
    'kit_slot': ('frames', 102, 72, 40, 40),         # 무기 칸
    'kit_slot_hot': ('frames', 148, 72, 40, 40),     # 든 무기 칸 (흰·청록 이중 선 + 모서리 결정)
    'kit_key': ('frames', 80, 86, 12, 12),           # 키캡
    'crystal': ('frames', 78, 23, 16, 14),           # 큰 판 모서리 결정
    # 막대
    'gauge_l': ('bars', 6, 7, 16, 25),
    'gauge_r': ('bars', 32, 7, 16, 25),
    'needle': ('bars', 37, 60, 5, 22),
    # 아이콘
    'heart': ('icons', 19, 6, 14, 13),
    'gem': ('icons', 57, 7, 5, 10),
    'potion_on': ('icons', 108, 6, 9, 13),
    'potion_off': ('icons', 122, 6, 9, 13),
    'dash_on': ('icons', 174, 8, 14, 9),
    'dash_off': ('icons', 193, 8, 14, 9),
    'shard': ('icons', 23, 37, 6, 12),
    'diamond': ('icons', 55, 39, 10, 8),
    'map_visited': ('icons', 73, 39, 10, 8),
    'map_current': ('icons', 87, 39, 10, 8),
    'map_unknown': ('icons', 101, 39, 10, 8),
    'map_boss': ('icons', 115, 39, 10, 8),
    'map_gold': ('icons', 129, 39, 10, 8),
    'map_haze': ('icons', 143, 39, 10, 8),
    'map_shop': ('icons', 157, 39, 10, 8),
    'dot_on': ('icons', 184, 40, 5, 5),
    'dot_off': ('icons', 193, 40, 5, 5),
    'combo_off': ('icons', 6, 75, 11, 11),
    'combo_on': ('icons', 21, 75, 11, 11),
    'combo_fin': ('icons', 36, 75, 11, 11),
    'cursor': ('icons', 58, 75, 4, 12),
    'reticle_ready': ('icons', 89, 67, 28, 28),
    'reticle_wait': ('icons', 123, 67, 28, 28),
    # 증강 카드
    'card_common': ('cards', 6, 6, 150, 210),
    'card_rare': ('cards', 166, 6, 150, 210),
    'card_legendary': ('cards', 326, 6, 150, 210),
    'step_on': ('cards', 226, 230, 12, 6),
    'step_off': ('cards', 244, 230, 12, 6),
}


def key_dim():
    """꺼진 키캡: 시트의 키캡에서 선을 한 단계씩 어둡게 (흰 -> 회색 -> 남색 3 -> 남색 2 -> 남색 1)."""
    a = part(*PARTS['kit_key'])
    out = a.copy()
    for src, dst in ((WHITE, GREY), (GREY, N3), (N3, N2), (N2, N1)):
        out[(a[:, :, :3] == src).all(axis=2) & (a[:, :, 3] == 255), :3] = dst
    return out


def tag_tall(extra=8):
    """이름표 띠(시트 4번, 32x12)를 글자(28px)가 들어가게 높인다: 가장 넓은 가운데 줄을 extra번 반복 -> 32x20(화면 64x40).
    게임은 가로 3칸(양끝 8점 + 가운데 반복)으로 그린다."""
    a = part('frames', 200, 24, 32, 12)
    return np.concatenate([a[:6], np.repeat(a[5:6], extra, axis=0), a[6:]])


def strip_hot(extra=8):
    """고른 메뉴 띠(시트 5번 아래, 64x15)의 몸통: 흰 윗선·청록 밑선·오른쪽 아래 청록 모서리는 그대로, 글자(28px)가 들어가게
    가운데 줄을 extra번 반복 -> 높이 22점(44px). 왼쪽 끝의 결정 칼날은 띠와 붙어 있어 늘릴 수 없으므로 떼어 내고,
    게임이 결정 덩어리(crystal)를 띠 왼쪽에 겹쳐 그린다. 왼쪽 끝은 흰 세로선 한 점."""
    a = part('frames', 6, 94, 64, 15)[1:, 16:]
    a = np.concatenate([a[:8], np.repeat(a[7:8], extra, axis=0), a[8:]])
    left = np.zeros((a.shape[0], 1, 4), np.uint8)
    left[:-1, 0] = (*WHITE, 255)
    left[-1, 0] = (*C_MID, 255)
    return np.concatenate([left, a], axis=1)


def frame_kit():
    """얇은 막대 틀(8x8, 모서리 3): 작은 HUD 틀과 같은 말투로 바깥 흰 1점(모서리 한 점 깎음) + 남색 3 한 점 + 속 남색 1."""
    a = rows([(WHITE, 1), (N3, 1), (N1, 4), (N3, 1), (WHITE, 1)], 8)
    a[:, 0] = a[:, 7] = (*WHITE, 255)
    a[1:7, 1] = a[1:7, 6] = (*N3, 255)
    for y, x in ((0, 0), (0, 7), (7, 0), (7, 7)):
        a[y, x] = 0
    return a


def gauge_body():
    """게이지 몸통(가로 반복 조각): 시트 3번의 줄 구성(흰 1 / 남색 3 / 남색 2 / 속 / 남색 2 / 남색 3 / 흰 1) 그대로,
    속 높이만 8 -> 10점(화면 20px, 막대 속 무늬 높이)으로."""
    return rows([(WHITE, 1), (N3, 1), (N2, 1), (N1, 10), (N2, 1), (N3, 1), (WHITE, 1)], 16)


def hp_frame(inner_w=190, inner_h=12, cap=8):
    """체력 막대 틀: 시트 7번(위 흰 1 / 남색 3 한 줄 / 속 / 아래 흰 1, 오른쪽 아래를 사선으로 자름)을 속 높이 12점(24px),
    속 너비 190점(380px)으로. 속은 투명(게임이 막대를 먼저 그리고 틀을 덮는다). 사선 끝 조각의 속은 남색 1로 막아
    막대가 사선 밖으로 나오지 않게 한다. 왼쪽 끝은 흰 세로선 한 점."""
    h = inner_h + 3
    w = 1 + inner_w + cap
    a = np.zeros((h, w, 4), np.uint8)
    a[0, :] = (*WHITE, 255)
    a[1, 1:] = (*N3, 255)
    a[h - 1, :] = (*WHITE, 255)
    a[:, 0] = (*WHITE, 255)
    x0 = 1 + inner_w                                  # 끝 조각이 시작하는 열
    cut0 = h - 6                                      # 이 줄부터 한 줄에 한 점씩 깎는다
    for y in range(h):
        cut = max(0, y - cut0 + 1)
        last = w - 1 - cut
        if 1 < y < h - 1:
            a[y, x0:last] = (*N1, 255)
        a[y, last + 1:] = 0
        a[y, last] = (*WHITE, 255)
        if cut and y < h - 1:
            a[y, last - 1] = (*WHITE, 255)            # 사선은 두 점 굵기 (시트와 같다)
    a[h - 1, w - 6:] = 0
    return a


def boss_caps():
    """보스 막대 양끝 결정: 시트 9번의 끝 3열(청록 결정)을 막대 높이 8점(16px) + 위아래 선 한 점씩 = 10줄로 늘린다(가운데 줄 반복)."""
    src = part('bars', 58, 109, 16, 6)
    left, right = src[:, :3], src[:, 13:]
    order = [0, 1, 2, 2, 2, 2, 3, 3, 4, 5]
    return left[order], right[order]


FILL_HEIGHTS = (8, 12, 16, 20, 24)
# 막대 속 무늬: (윗줄 밝은 색, 몸, 아래 그림자). 시트 6번의 구성(윗줄 1점 밝게, 아래 그림자)을 모든 색에 쓴다.
# 빨강·주황의 윗줄은 시트에서 흰색이었는데(팔레트에 밝은 빨강이 없어서) 너무 튀어 몸 색을 흰색 쪽으로 반쯤 섞었다(보고서 4-3).
FILLS = {
    'red': (mix(RED, WHITE, 0.45), RED, RED_LO),
    'gray': (WHITE, GREY, mix(GREY, N3, 0.6)),
    'cyan': (C_HI, C_MID, C_LO),
    'orange': (mix(ORANGE, WHITE, 0.45), ORANGE, mix(ORANGE, RED_LO, 0.55)),
    'blue': ((176, 204, 250), (110, 150, 232), (52, 78, 150)),
    'boss': (mix(RED, WHITE, 0.3), (206, 44, 60), (110, 22, 36)),
    'white': ((255, 255, 255), WHITE, GREY),
    'yellow': ((255, 236, 170), GOLD, GOLD_LO),
    'violet': ((216, 196, 255), (170, 132, 250), (92, 66, 170)),
    'empty': (N1, N2, N2),
}


def fill(color, height_px):
    hi, mid, lo = FILLS[color]
    n = height_px // SCALE
    shadow = 1 if n <= 6 else 2 if n <= 10 else 3
    return rows([(hi, 1), (mid, n - 1 - shadow), (lo, shadow)], 512)


def main():
    for name, spec in PARTS.items():
        save(part(*spec), name)
    save(key_dim(), 'kit_key_dim')
    save(tag_tall(), 'tag')
    save(strip_hot(), 'strip_hot')
    save(frame_kit(), 'kit_frame')
    save(gauge_body(), 'gauge_body')
    save(hp_frame(), 'hp_frame')
    left, right = boss_caps()
    save(left, 'boss_l')
    save(right, 'boss_r')
    for color in FILLS:
        for h in FILL_HEIGHTS:
            save(fill(color, h), f'fill_{color}_{h}')
    print('saved', len(PARTS) + 8 + len(FILLS) * len(FILL_HEIGHTS), 'files -> assets/ui/uc_*.png')


if __name__ == '__main__':
    main()
