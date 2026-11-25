"""이벤트 방 소품을 만든다 (v8 계획 5-4, 2026-11-25). code-drawn + 우리 그림의 색 바꾸기.

- 헤이즈 샘: 돌 그릇에 고인 헤이즈. 논리 64x56을 정수 2배(128x112)로. 물결 2장 + 마른 모습 1장.
  assets/ui/event_spring_1.png, event_spring_2.png, event_spring_dry.png
- 떠돌이 죄수: 보관인 그림(Codex T22, assets/sprites/unified/npc_keeper_idle_1~2.png)의 색을 바꾼 것.
  청록 옷 -> 바랜 적갈색, 전체를 조금 어둡게. assets/sprites/unified/npc_drifter_idle_1~2.png
- 미니맵 표시: assets/ui/hud_map_event.png (20x16, 물음표)
- 구역별 장치(5-5): assets/ui/device_crate.png·device_crate_broken.png(슬럼 상자), device_vent.png·device_vent_hot.png(공장 증기 분출구),
  device_laser.png(탑 감시 레이저의 머리), device_crack.png(슬럼 부서지는 발판의 금 간 표시)

사용: python tools/make_event_props.py
"""
import colorsys
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from make_icons import Canvas, K, shade, up2  # noqa: E402

UI = os.path.join(ROOT, 'assets', 'ui')
UNIFIED = os.path.join(ROOT, 'assets', 'sprites', 'unified')

STONE = ((30, 36, 54), (58, 68, 96), (96, 110, 142), (148, 162, 190))      # 어두움 -> 밝음
HAZE = ((14, 92, 100), (30, 168, 164), (92, 232, 214), (214, 255, 246))
DRY = ((24, 28, 40), (40, 46, 62), (62, 70, 90), (92, 102, 124))


def spring(frame):
    """frame 1·2: 물결이 다른 두 장, 'dry': 다 쓴 샘 (빛이 꺼지고 바닥이 드러난다)."""
    cv = Canvas(64, 56)
    dry = frame == 'dry'
    d, m, l, h = DRY if dry else STONE
    # 받침 (아래로 넓어지는 세 단)
    cv.rect(18, 46, 45, 53, m)
    cv.rect(18, 46, 45, 47, l)
    cv.rect(43, 48, 45, 53, d)
    cv.rect(12, 51, 51, 55, d)
    cv.rect(12, 51, 51, 51, m)
    cv.rect(26, 38, 37, 46, m)                          # 기둥
    cv.rect(26, 38, 28, 46, l)
    cv.rect(35, 38, 37, 46, d)
    # 그릇: 위가 넓은 사다리꼴
    for i, y in enumerate(range(26, 39)):
        inset = i * 14 // 13
        cv.rect(6 + inset, y, 57 - inset, y, m)
        cv.px(6 + inset, y, l)
        cv.px(7 + inset, y, l)
        cv.px(57 - inset, y, d)
        cv.px(56 - inset, y, d)
    cv.rect(4, 22, 59, 25, l)                           # 테두리
    cv.rect(4, 22, 59, 22, h)
    cv.rect(4, 25, 59, 25, m)
    for x in (10, 22, 41, 53):                          # 테두리의 금(돌 이음매)
        cv.rect(x, 23, x, 25, d)
    cv.rect(14, 30, 15, 33, d)                          # 그릇의 홈 (헤이즈가 스며 빛난다)
    cv.rect(31, 31, 32, 36, d)
    cv.rect(48, 30, 49, 33, d)
    if dry:
        cv.rect(8, 20, 55, 21, d)                       # 빈 바닥
        cv.rect(8, 21, 55, 21, m)
        for x in (16, 30, 44):
            cv.px(x, 20, m)
    else:
        hd, hm, hl, hh = HAZE
        cv.rect(14, 30, 15, 33, hm)
        cv.rect(31, 31, 32, 36, hm)
        cv.rect(48, 30, 49, 33, hm)
        cv.px(31, 31, hl)
        cv.rect(8, 19, 55, 21, hm)                      # 고인 헤이즈
        cv.rect(8, 21, 55, 21, hd)
        shift = 0 if frame == 1 else 5
        for x0 in range(10 + shift, 54, 11):            # 물결의 밝은 줄
            cv.rect(x0, 19, min(54, x0 + 4), 19, hl)
            cv.px(x0 + 1, 19, hh)
    cv.outline()
    if not dry:                                         # 김과 알갱이는 외곽선 없이 (빛처럼 보이게)
        hd, hm, hl, hh = HAZE
        f = frame - 1
        for k, (x, top) in enumerate(((17, 10), (27, 5), (38, 8), (47, 12))):     # 위로 오르는 가는 김 (끊어진 세로줄)
            for y in range(top + f * 2, 17, 4):
                dx = 1 if (y // 4 + k + f) % 2 else 0
                cv.px(x + dx, y, hl if y > top + 5 else hm)
                cv.px(x + dx, y + 1, hm if y > top + 5 else hd)
        cv.px(22, 13 - f * 3, hh)                       # 떠오르는 알갱이
        cv.px(43, 11 + f * 2, hh)
        cv.px(33, 15 - f * 2, hl)
    return cv


def drifter(src):
    """보관인 그림의 색을 바꾼다: 청록·푸른 계열은 바랜 적갈색으로, 전체를 조금 어둡게. 알파는 그대로."""
    a = np.array(Image.open(src).convert('RGBA'))
    out = a.copy()
    h, w = a.shape[:2]
    for y in range(h):
        for x in range(w):
            r, g, b, al = (int(v) for v in a[y, x])
            if al == 0:
                continue
            hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if 0.38 <= hh <= 0.72 and ss > 0.18:        # 청록~파랑 (옷·머리띠)
                hh, ss = 0.03, min(1.0, ss * 0.85)
            vv *= 0.9
            nr, ng, nb = colorsys.hsv_to_rgb(hh, ss, vv)
            out[y, x] = (int(nr * 255), int(ng * 255), int(nb * 255), al)
    return out


def map_mark():
    """미니맵의 이벤트 방 표시: 20x16(논리 10x8)에 물음표."""
    cv = Canvas(10, 8)
    c = (214, 255, 236)
    for x, y in ((3, 1), (4, 0), (5, 0), (6, 1), (6, 2), (5, 3), (4, 4), (4, 6)):
        cv.px(x, y, c)
    return cv


# ---------------------------------------------------------------- 구역별 장치 (v8 5-5)
WOOD = ((44, 30, 24), (92, 62, 40), (140, 98, 58), (188, 142, 88))
IRON = ((26, 30, 44), (54, 62, 84), (92, 104, 132), (150, 164, 192))
HOT = ((120, 44, 24), (220, 110, 40), (255, 190, 90), (255, 240, 200))
BEAM = ((92, 20, 36), (200, 44, 60), (255, 110, 110), (255, 226, 214))


def crate(broken=False):
    """슬럼 상자: 논리 30x30(60x60). 널빤지 + 쇠 모서리. broken은 부서진 널 조각 더미."""
    cv = Canvas(30, 30)
    d, m, l, h = WOOD
    id_, im, il, ih = IRON
    if broken:
        cv.rect(3, 26, 26, 28, d)                        # 바닥에 남은 밑판
        cv.rect(3, 26, 26, 26, m)
        cv.poly([(4, 26), (9, 17), (12, 18), (8, 26)], m)       # 기울어진 널 조각
        cv.poly([(17, 26), (23, 19), (26, 21), (21, 26)], l)
        cv.rect(12, 22, 16, 25, d)
        cv.rect(12, 22, 16, 22, m)
        cv.px(9, 17, h)
        cv.px(23, 19, h)
        cv.rect(2, 27, 4, 28, im)                        # 떨어진 쇠 모서리
        cv.px(2, 27, il)
        cv.outline()
        return cv
    cv.rect(2, 3, 27, 28, m)
    for y in (3, 11, 20):                                # 널빤지 세 장 (위가 밝다)
        cv.rect(2, y, 27, y, l)
    for y in (10, 19, 28):
        cv.rect(2, y, 27, y, d)
    cv.rect(2, 3, 27, 3, h)
    cv.line(6, 6, 23, 25, d, 2)                          # 대각선 보강대
    cv.line(6, 5, 23, 24, l)
    for x0, y0 in ((2, 3), (23, 3), (2, 24), (23, 24)):  # 쇠 모서리
        cv.rect(x0, y0, x0 + 4, y0 + 4, im)
        cv.rect(x0, y0, x0 + 4, y0, il)
        cv.px(x0 + 2, y0 + 2, ih)
    cv.rect(26, 8, 27, 23, d)                            # 오른쪽 그늘
    cv.outline()
    return cv


def vent(hot=False):
    """공장 증기 분출구: 논리 36x10(72x20). 바닥에 박힌 쇠 격자. hot은 분출 직전(틈이 달아오른다)."""
    cv = Canvas(36, 10)
    d, m, l, h = IRON
    cv.rect(1, 3, 34, 8, m)
    cv.rect(1, 3, 34, 3, l)
    cv.rect(1, 8, 34, 8, d)
    cv.rect(3, 1, 32, 2, l)                              # 위로 솟은 테
    cv.rect(3, 1, 32, 1, h)
    glow = HOT[2] if hot else d
    core = HOT[3] if hot else IRON[0]
    for x in range(5, 31, 5):                            # 틈 다섯
        cv.rect(x, 4, x + 2, 7, glow)
        cv.rect(x + 1, 5, x + 1, 6, core)
    for x in (2, 33):                                    # 나사
        cv.px(x, 5, h)
    cv.outline()
    return cv


def laser_head():
    """탑 감시 레이저의 머리: 논리 26x16(52x32). 천장에 매달린 쇠 틀과 아래를 보는 붉은 렌즈."""
    cv = Canvas(26, 16)
    d, m, l, h = IRON
    cv.rect(9, 0, 16, 4, m)                              # 천장 걸이
    cv.rect(9, 0, 10, 4, l)
    cv.rect(3, 4, 22, 11, m)                             # 몸통
    cv.rect(3, 4, 22, 4, h)
    cv.rect(3, 5, 4, 11, l)
    cv.rect(21, 5, 22, 11, d)
    cv.rect(6, 7, 8, 8, d)                               # 옆 통풍구
    cv.rect(17, 7, 19, 8, d)
    cv.rect(9, 11, 16, 14, d)                            # 렌즈 틀
    cv.rect(10, 12, 15, 15, BEAM[1])
    cv.rect(11, 13, 14, 15, BEAM[2])
    cv.rect(12, 14, 13, 15, BEAM[3])
    cv.outline()
    return cv


def crack():
    """부서지는 발판 표시: 논리 30x6(60x12). 발판 윗면에 덮는 금과 녹슨 얼룩 (칸마다 하나)."""
    cv = Canvas(30, 6)
    dark, rust = (16, 20, 34), (150, 86, 52)
    for x, y in ((4, 0), (5, 1), (5, 2), (6, 3), (13, 0), (14, 1), (15, 1), (16, 2), (16, 3), (17, 4), (24, 0), (24, 1), (23, 2), (23, 3)):
        cv.px(x, y, dark)
    for x, y in ((9, 0), (10, 0), (20, 0), (21, 0), (21, 1), (27, 0)):
        cv.px(x, y, rust)
    return cv


def main():
    Image.fromarray(up2(crack().a), 'RGBA').save(os.path.join(UI, 'device_crack.png'))
    for name, cv in (('device_crate', crate()), ('device_crate_broken', crate(True)), ('device_vent', vent()),
                     ('device_vent_hot', vent(True)), ('device_laser', laser_head())):
        Image.fromarray(up2(cv.a), 'RGBA').save(os.path.join(UI, name + '.png'))
    for frame in (1, 2, 'dry'):
        Image.fromarray(up2(spring(frame).a), 'RGBA').save(os.path.join(UI, f'event_spring_{frame}.png'))
    for n in (1, 2):
        arr = drifter(os.path.join(UNIFIED, f'npc_keeper_idle_{n}.png'))
        Image.fromarray(arr, 'RGBA').save(os.path.join(UNIFIED, f'npc_drifter_idle_{n}.png'))
    Image.fromarray(up2(map_mark().a), 'RGBA').save(os.path.join(UI, 'hud_map_event.png'))
    print('saved: event_spring_1·2·dry, npc_drifter_idle_1·2, hud_map_event')


if __name__ == '__main__':
    main()
