"""PixelLab '교도소 철판' UI 판을 게임 부품으로 굽는다 (2026-11-26, docs/opus/TASKS.md 3차 O8 재시험).

원본: assets/sprites/pixellab/ui_plate_v1/kit/kit_<시안>.png (create_ui_asset 512x512, 부품 12개를 한 장에, 도트 1칸 = 1px)
      assets/sprites/pixellab/ui_plate_v1/kit/cards_<시안>.png (create_ui_asset 448x600, 카드 틀 넷)
결과: assets/ui/upx_*.png — 지금 부품(uc_*·up_*)과 이름·크기가 같다(config.UI_SKIN = 'plate'). 화면에는 최근접 2배.
PixelLab 판이 없는 작은 부품(하트·물약·대시·미니맵 칸·막대 속 무늬·조준점 등)은 만들지 않는다: hud_kit이 코드 철판(up_*)을 쓴다.

굽는 법: 부품마다 알파 덩어리로 잘라 fit()으로 원하는 크기에 맞춘다 — 네 모서리(cx x cy)는 그대로, 변은 원본 변의 가운데에서
필요한 길이만큼 잘라 쓰고(늘이지 않는다), 가운데는 원본 가운데 색(가장 흔한 색) 한 가지로 메운다(이어 붙여도 무늬가 끊기지 않게).

사용: python tools/apply_ui_plate.py [--look a|b|c] [--out assets/ui]
"""
import argparse
import collections
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, 'assets', 'sprites', 'pixellab', 'ui_plate_v1', 'kit')
UI = os.path.join(ROOT, 'assets', 'ui')
sys.path.insert(0, os.path.join(ROOT, 'tools'))

# 부품 판의 알파 덩어리 -> 이름 (create_ui_asset pieces 순서: 위에서 아래, 왼쪽에서 오른쪽으로 정렬한 순서)
KIT_ORDER = ['window', 'plate', 'key', 'tag', 'button', 'selected', 'slot', 'slot_hot', 'bar', 'tube', 'boss', 'sign']
CARD_ORDER = ['common', 'rare', 'legendary', 'curse']
KEY_FROM_BUTTON = ('a',)


def pieces(path, order, min_area=200):
    """알파 덩어리를 (위, 왼쪽) 순으로 정렬해 이름을 붙인다. 같은 줄(위 가장자리 차이 12px 안)은 왼쪽부터."""
    from scipy import ndimage
    a = np.array(Image.open(path).convert('RGBA'))
    lab, _n = ndimage.label(a[:, :, 3] > 0)
    boxes = [sl for sl in ndimage.find_objects(lab) if (sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start) >= min_area]
    boxes.sort(key=lambda sl: (sl[0].start, sl[1].start))
    rows, cur = [], []
    for sl in boxes:
        if cur and sl[0].start - cur[0][0].start > 12:
            rows.append(cur)
            cur = []
        cur.append(sl)
    rows.append(cur)
    ordered = [sl for row in rows for sl in sorted(row, key=lambda s: s[1].start)]
    if len(ordered) != len(order):
        raise SystemExit(f'{os.path.basename(path)}: 덩어리 {len(ordered)}개, 이름 {len(order)}개 — 판을 눈으로 보고 KIT_ORDER를 고친다')
    out = {}
    for name, sl in zip(order, ordered):
        piece = a[sl].copy()
        piece[lab[sl] == 0] = 0                                  # 이웃 덩어리 조각이 섞이지 않게
        out[name] = piece
    return out


def center_color(p):
    """가운데 1/3 영역에서 가장 흔한 불투명 색."""
    h, w = p.shape[:2]
    c = p[h // 3: 2 * h // 3, w // 3: 2 * w // 3].reshape(-1, 4)
    c = [tuple(v) for v in c if v[3] > 0]
    return collections.Counter(c).most_common(1)[0][0] if c else (29, 34, 43, 255)


def fit(p, w, h, cx, cy, fill=True, uniform=False):
    """원본 조각 p를 w x h로: 모서리 cx x cy 그대로, 변은 원본 가운데에서 잘라 쓰고, 가운데는 한 색(fill) 또는 원본 가운데를 잘라.
    uniform: 변을 모서리 바로 안쪽 한 줄로 고르게 이어 붙인다 (원본 변 가운데에 고리·띠 같은 장식이 있을 때)."""
    sh, sw = p.shape[:2]
    if uniform:
        cx, cy = min(cx, sw // 2 - 1, w // 2), min(cy, sh // 2 - 1, h // 2)
        q = np.zeros((sh, 2 * cx + 1, 4), np.uint8)
        q[:, :cx], q[:, cx], q[:, cx + 1:] = p[:, :cx], p[:, cx], p[:, sw - cx:]
        r = np.zeros((2 * cy + 1, q.shape[1], 4), np.uint8)
        r[:cy], r[cy], r[cy + 1:] = q[:cy], q[cy], q[sh - cy:]
        p, sh, sw = r, r.shape[0], r.shape[1]
    cx, cy = min(cx, (sw - 1) // 2, w // 2), min(cy, (sh - 1) // 2, h // 2)   # 원본 가운데가 적어도 한 줄은 남게 (이어 붙일 조각)
    out = np.zeros((h, w, 4), np.uint8)
    mw, mh = w - 2 * cx, h - 2 * cy

    def mid(length, total, corner):
        start = max(corner, (total - length) // 2)
        return start, min(total - corner, start + length)

    if fill:
        out[cy:h - cy, cx:w - cx] = center_color(p)
    else:
        x0, x1 = mid(mw, sw, cx)
        y0, y1 = mid(mh, sh, cy)
        out[cy:cy + (y1 - y0), cx:cx + (x1 - x0)] = p[y0:y1, x0:x1]
    # 변: 위·아래 (가로 가운데), 왼쪽·오른쪽 (세로 가운데). 원본이 짧으면 가운데 조각을 이어 붙인다
    for (dst_y, src_y) in ((0, 0), (h - cy, sh - cy)):
        x = cx
        while x < w - cx:
            x0, x1 = mid(w - cx - x, sw, cx)
            n = min(x1 - x0, w - cx - x)
            out[dst_y:dst_y + cy, x:x + n] = p[src_y:src_y + cy, x0:x0 + n]
            x += n
    for (dst_x, src_x) in ((0, 0), (w - cx, sw - cx)):
        y = cy
        while y < h - cy:
            y0, y1 = mid(h - cy - y, sh, cy)
            n = min(y1 - y0, h - cy - y)
            out[y:y + n, dst_x:dst_x + cx] = p[y0:y0 + n, src_x:src_x + cx]
            y += n
    out[:cy, :cx] = p[:cy, :cx]
    out[:cy, w - cx:] = p[:cy, sw - cx:]
    out[h - cy:, :cx] = p[sh - cy:, :cx]
    out[h - cy:, w - cx:] = p[sh - cy:, sw - cx:]
    return out


def darken(a, k=0.62):
    out = a.copy()
    out[:, :, :3] = (out[:, :, :3].astype(float) * k).astype(np.uint8)
    return out


def save(a, name, out=UI):
    im = Image.fromarray(np.ascontiguousarray(a), 'RGBA')
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(out, f'upx_{name}.png'))
    return name


def build(look='a', out=UI):
    kit = pieces(os.path.join(KIT, f'kit_{look}.png'), KIT_ORDER)
    made = []
    # 9칸 판 (크기는 hud_kit.KITS: 그림 한 변/2, 모서리/2)
    made.append(save(fit(kit['window'], 48, 48, 12, 12), 'kit_panel', out))
    made.append(save(fit(kit['plate'], 24, 24, 6, 6), 'kit_plate', out))
    made.append(save(fit(kit['slot'], 40, 40, 8, 8), 'kit_slot', out))
    made.append(save(fit(kit['slot_hot'], 40, 40, 8, 8), 'kit_slot_hot', out))
    key = kit['button'] if look in KEY_FROM_BUTTON else kit['key']   # 시안 a는 'key' 칸에 열쇠 그림이 나와 버튼 조각으로
    made.append(save(fit(key, 12, 12, 4, 4), 'kit_key', out))
    made.append(save(darken(fit(key, 12, 12, 4, 4)), 'kit_key_dim', out))
    made.append(save(fit(kit['bar'], 8, 8, 3, 3), 'kit_frame', out))
    # 이름표 64x40, 고른 메뉴 띠 98x44 (hud_kit.strip은 철판 스킨에서 양끝 16px을 그대로 둔다)
    made.append(save(fit(kit['tag'], 32, 20, 8, 7), 'tag', out))
    strip = fit(kit['button'], 49, 22, 8, 8)                    # 가운데는 맨 철판 (글자가 줄무늬에 묻히지 않게)
    hot = fit(kit['selected'], 49, 22, 8, 8, fill=False)
    strip[:, 41:] = hot[:, 41:]                                  # 오른쪽 끝 8점만 경고 줄무늬 판
    strip[18:20, 2:41] = (226, 178, 58, 255)                     # 노란 밑줄 2점 (경고 노랑)
    strip[20, 2:41] = (138, 102, 26, 255)
    made.append(save(strip, 'strip_hot', out))
    # 체력 막대 틀 398x30: 속(화면 2..380 x 2..26 = 1배 1..190 x 1..13)은 비운다 (막대 위에 그린다)
    hp = fit(kit['bar'], 199, 15, 8, 4)
    hp[2:13, 2:191] = 0
    made.append(save(hp, 'hp_frame', out))
    # 게이지: 몸통 32x32 (가로로 이어 붙인다), 양끝 32x50 (관 끝 쇠고리)
    tube = kit['tube']
    th, tw = tube.shape[:2]
    made.append(save(fit(tube[:, tw // 2 - 8: tw // 2 + 8], 16, 16, 0, 5), 'gauge_body', out))
    cap = np.zeros((25, 16, 4), np.uint8)
    cap[(25 - min(25, th)) // 2:(25 - min(25, th)) // 2 + min(25, th)] = tube[:min(25, th), :16]
    made.append(save(cap, 'gauge_l', out))
    cap = np.zeros((25, 16, 4), np.uint8)
    cap[(25 - min(25, th)) // 2:(25 - min(25, th)) // 2 + min(25, th)] = tube[:min(25, th), tw - 16:]
    made.append(save(cap, 'gauge_r', out))
    # 보스 체력 막대 틀 (새 부품, 화면 976x28: 막대 960x16 둘레 8·6px). 막대는 이 위에 그린다
    made.append(save(fit(kit['boss'], 488, 14, 16, 4, uniform=True), 'boss_frame', out))
    # 로고 판 472x200 (글자는 tools/make_title_plate.py가 찍는다)
    made.append(save(fit(kit['sign'], 236, 100, 22, 14, fill=True), 'logo_plate', out))
    # 카드 틀 300x420 (카드 넷)
    cards_path = os.path.join(KIT, f'cards_{look}.png')
    if os.path.exists(cards_path):
        cards = pieces(cards_path, CARD_ORDER)
        for kind in CARD_ORDER:
            made.append(save(fit(cards[kind], 150, 210, 40, 40), f'card_{kind}', out))
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--look', default='a')
    ap.add_argument('--out', default=UI)
    a = ap.parse_args()
    made = build(a.look, a.out)
    print(f'{len(made)}개 (시안 {a.look}) -> {a.out}:', ', '.join(made))


if __name__ == '__main__':
    main()
