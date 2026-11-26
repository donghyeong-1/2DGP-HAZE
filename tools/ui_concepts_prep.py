"""PixelLab 컨셉 그림을 잘라 화면용 2배 조각으로 (assets/sprites/pixellab/ui_concepts_v2/<컨셉>/parts/)."""
import os, sys
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from apply_ui_plate import fit
B = os.path.join(ROOT, 'assets', 'sprites', 'pixellab', 'ui_concepts_v2')

def save2(a, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = Image.fromarray(np.ascontiguousarray(a), 'RGBA'); im = im.crop(im.getchannel('A').getbbox() or (0, 0, im.width, im.height))
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(path)

def load(p):
    return np.array(Image.open(os.path.join(B, p)).convert('RGBA'))

def crop(a, x, y, w, h):
    return a[y:y + h, x:x + w].copy()

# A 안개
for n in ('logo_s8', 'ember_s7', 'divider_white_s9', 'divider_cyan_s9', 'divider_gold_s9', 'divider_red_s9', 'mist_pool_s9'):
    save2(load(f'a_mist/{n}.png'), os.path.join(B, 'a_mist', 'parts', n.rsplit('_s', 1)[0] + '.png'))
# B 단말
t = load('b_terminal/sheet_1x.png')
P = os.path.join(B, 'b_terminal', 'parts')
save2(fit(crop(t, 6, 6, 91, 126), 180, 250, 22, 22, fill=True), os.path.join(P, 'card.png'))
for name, (x, y, w, h) in {'header': (105, 6, 146, 14), 'header_red': (6, 195, 100, 14), 'header_gold': (6, 218, 100, 14)}.items():
    a = crop(t, x, y, w, h)
    save2(fit(a, 176, a.shape[0], 8, 6), os.path.join(P, name + '.png'))
save2(crop(t, 105, 28, 31, 31), os.path.join(P, 'bracket_steel.png'))
brk = crop(t, 145 + 4, 28 + 4, 16, 16)                  # 모니터 조각 안쪽의 가는 청록 꺾쇠만 (어두운 화면 점은 뺀다)
brk[brk[:, :, 1] < 150] = 0
save2(brk, os.path.join(P, 'bracket.png'))
save2(crop(t, 145, 28, 106, 61), os.path.join(P, 'screen_brackets.png'))
save2(crop(t, 105, 98, 71, 16), os.path.join(P, 'lamps.png'))
save2(crop(t, 185, 98, 14, 21), os.path.join(P, 'cursor.png'))
save2(crop(t, 6, 175, 245, 7), os.path.join(P, 'line.png'))
save2(load('b_terminal/logo_s5.png'), os.path.join(P, 'logo.png'))
# C 기록
r = load('c_record/sheet_1x.png')
P = os.path.join(B, 'c_record', 'parts')
card = fit(crop(r, 6, 6, 91, 125), 180, 250, 30, 30, fill=True)
card[30:220, 30:150] = (168, 151, 127, 255)             # 가운데는 종이색 (원본 가운데의 회색 얼룩 대신)
save2(card, os.path.join(P, 'card.png'))
for name, box in {'stamp_red': (108, 8, 45, 45), 'stamp_blue': (158, 8, 45, 45), 'stamp_gold': (208, 8, 44, 45),
                  'stamp_rect': (107, 62, 62, 28), 'clip': (195, 62, 20, 47), 'tab': (107, 100, 76, 21),
                  'underline': (8, 147, 149, 8), 'check': (172, 137, 26, 26)}.items():
    save2(crop(r, *box), os.path.join(P, name + '.png'))
save2(load('c_record/logo_s8.png'), os.path.join(P, 'logo.png'))
print('ok')
