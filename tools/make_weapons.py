"""무기 그림(식칼 투사체 8방향, 건틀릿 충격파, 무기 아이콘)을 코드로 그리고, 던지기·주먹 자세 프레임을 게임 폴더로 옮긴다.

실행 중 회전은 금지(docs/pixel_rules.md)라서 식칼은 45도마다 미리 그린다. 방향 번호 k는 각도 k*45도(0 = 오른쪽, 반시계).
주먹 자세는 Codex T05의 맨손 공격 4프레임(assets/sprites/forge/n09_attack_v3)을 그대로 쓴다 (던지기·건틀릿 공용).

사용: python tools/make_weapons.py
결과: assets/sprites/unified/proj_knife_0~7.png, proj_blast_s|m|l_1~2.png, n09_punch_1~4.png, assets/ui/icon_w_*.png
"""
import math
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
UNIFIED = ROOT / "assets" / "sprites" / "unified"
UI = ROOT / "assets" / "ui"

OUTLINE = (12, 14, 22, 255)
STEEL_HI = (240, 244, 250, 255)
STEEL = (186, 196, 210, 255)
STEEL_LO = (112, 122, 138, 255)
HANDLE = (52, 44, 52, 255)
HANDLE_LO = (32, 28, 34, 255)
CYAN = (90, 210, 240, 255)
CYAN_LO = (40, 130, 170, 255)
WHITE = (250, 252, 255, 255)
RUST = (150, 96, 70, 255)


def outline(img):
    """불투명 픽셀 둘레(상하좌우)에 1px 어두운 외곽선을 두른다."""
    w, h = img.size
    src = img.load()
    out = img.copy()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] and src[nx, ny] != OUTLINE:
                    dst[x, y] = OUTLINE
                    break
    return out


# ---------------------------------------------------------------- 식칼 (8방향)
# 칼 한 자루를 '축을 따라 몇 칸째, 축에서 옆으로 몇 칸' 표로 정의한다 (오른쪽을 향한 칼, 끝이 +).
# 옆 칸 -1이 위쪽(빛을 받는 면)이다.
def knife_cells():
    cells = {}
    for i in range(0, 9):                       # 손잡이 9칸
        cells[(i, 0)] = HANDLE
        cells[(i, 1)] = HANDLE_LO
    for i in (3, 4):                            # 손잡이의 청록 천 감김
        cells[(i, 0)] = CYAN
        cells[(i, 1)] = CYAN_LO
    for s in (-1, 0, 1, 2):                     # 날밑
        cells[(9, s)] = STEEL_LO
    for i in range(10, 27):                     # 칼날 17칸: 위 밝음, 가운데 기본, 아래 그림자
        cells[(i, -1)] = STEEL_HI
        cells[(i, 0)] = STEEL
        cells[(i, 1)] = STEEL_LO
    for i in (27, 28):                          # 끝이 좁아진다
        cells[(i, -1)] = STEEL_HI
        cells[(i, 0)] = STEEL
    cells[(29, 0)] = STEEL_HI
    return cells


def draw_knife(k):
    """방향 k(0~7)의 칼. 밝은 면이 늘 위를 향하게 옆 방향을 고른다.
    대각선은 축 1칸 = (1,1) 이동이라 √2배 길어 보이므로 칸 수를 줄이고, 옆 칸은 가로 한 칸 이동으로 둔다(두께 유지)."""
    ang = k * 45
    dx, dy = round(math.cos(math.radians(ang))), round(math.sin(math.radians(ang)))
    diagonal = dx != 0 and dy != 0
    nx, ny = -dy, dx                              # 축을 반시계로 90도
    if ny < 0 or (ny == 0 and nx > 0):           # 위쪽을 가리키게 (밝은 면 = 위)
        nx, ny = -nx, -ny
    pts = {}
    for (i, s), color in knife_cells().items():
        if diagonal:
            a = int(i * 0.72)
            x, y = a * dx - nx * s, a * dy
        else:
            x, y = i * dx - nx * s, i * dy - ny * s
        if (x, y) not in pts or color in (STEEL_HI, CYAN):
            pts[(x, y)] = color
    minx = min(p[0] for p in pts)
    maxx = max(p[0] for p in pts)
    miny = min(p[1] for p in pts)
    maxy = max(p[1] for p in pts)
    img = Image.new("RGBA", (maxx - minx + 3, maxy - miny + 3), (0, 0, 0, 0))
    px = img.load()
    for (x, y), color in pts.items():
        px[x - minx + 1, (maxy - y) + 1] = color   # 그림 좌표는 아래로 증가 (게임 좌표는 위로 증가)
    return outline(img)


# ---------------------------------------------------------------- 건틀릿 충격파 (크기 3종 x 깜빡임 2장)
def draw_blast(r, phase):
    size = 2 * r + 5
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    c = size // 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c)
            ring = r - (2 if phase else 0)
            if ring - 3 <= d <= ring:
                px[x, y] = WHITE if d >= ring - 1 else CYAN
            elif ring - 7 <= d < ring - 3 and (x + y + phase) % 2 == 0:
                px[x, y] = CYAN_LO               # 고리 안쪽의 성긴 점 (반투명 대신 점묘)
            elif d <= r * 0.28:
                px[x, y] = WHITE if d <= r * 0.16 else CYAN
    # 앞으로 튀는 파편 (오른쪽이 진행 방향, 왼쪽 방향은 좌우 반전으로 그린다)
    for k in range(5):
        a = math.radians(-40 + k * 20)
        x = int(c + math.cos(a) * (r + 2 - phase))
        y = int(c - math.sin(a) * (r + 2 - phase))
        if 0 <= x < size and 0 <= y < size:
            px[x, y] = WHITE
    return outline(img)


# ---------------------------------------------------------------- 무기 아이콘 48x48
def icon_knife():
    img = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    k = draw_knife(1)                                       # 앞 위 45도 칼 세 자루를 부채꼴로 겹친다
    for ox, oy in ((2, 14), (12, 10), (20, 2)):
        img.alpha_composite(k, (ox, 48 - k.height - oy))
    return img


def icon_gauntlet():
    """옆에서 본 주먹(오른쪽이 앞): 왼쪽 손목 갑과 헤이즈 관, 가운데 손등 판, 오른쪽 손가락 마디, 아래 엄지."""
    img = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    px = img.load()
    for y in range(18, 34):                                  # 손목 갑
        for x in range(4, 18):
            px[x, y] = STEEL_LO if y > 30 else STEEL
    for x in range(6, 17, 4):                                # 손목의 청록 헤이즈 관
        for y in range(19, 33):
            px[x, y] = CYAN if y < 26 else CYAN_LO
    for y in range(12, 38):                                  # 손등 판
        for x in range(17, 36):
            px[x, y] = STEEL_HI if y < 16 else STEEL_LO if y > 33 else STEEL
    for y in range(14, 34):                                  # 손가락 마디 (앞쪽 둥근 끝)
        for x in range(36, 42):
            if not ((y < 16 or y > 31) and x > 39):
                px[x, y] = STEEL_LO if x > 39 else STEEL
    for y in (19, 24, 29):                                   # 손가락 사이 홈
        for x in range(33, 42):
            px[x, y] = STEEL_LO
    for y in range(36, 41):                                  # 엄지
        for x in range(20, 30):
            px[x, y] = STEEL_LO if y > 38 else STEEL
    for y in (20, 28):                                       # 리벳
        px[21, y] = OUTLINE
    for y in range(18, 31, 4):                               # 주먹 앞에서 튀는 충격
        px[45, y] = WHITE
        px[44, y + 1] = CYAN
    return outline(img)


def icon_pipe():
    img = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    px = img.load()
    for i in range(36):                           # 대각선 파이프 (굵기 4)
        x, y = 6 + i, 41 - i
        for t, color in enumerate((STEEL_HI, STEEL, STEEL, STEEL_LO)):
            if 0 <= x + t < 48:
                px[x + t, y] = color
    for i in range(6):                            # 손잡이 청록 천 감김
        x, y = 6 + i, 41 - i
        for t in range(4):
            px[x + t, y] = CYAN if t < 2 else CYAN_LO
    for t in range(4):                            # 녹슨 끝마개
        px[41 + t, 6] = RUST
        px[41 + t, 5] = RUST
    return outline(img)


def copy_punch():
    """Codex T05의 맨손 공격 4프레임을 n09_punch_1~4.png로 옮긴다 (던지기·건틀릿 공용 자세)."""
    src = ROOT / "assets" / "sprites" / "forge" / "n09_attack_v3" / "frames"
    for i in range(1, 5):
        shutil.copyfile(src / f"attack-{i}.png", UNIFIED / f"n09_punch_{i}.png")


def main():
    for k in range(8):
        draw_knife(k).save(UNIFIED / f"proj_knife_{k}.png")
    for name, r in (("s", 26), ("m", 34), ("l", 44)):
        for phase in (1, 2):
            draw_blast(r, phase - 1).save(UNIFIED / f"proj_blast_{name}_{phase}.png")
    icon_knife().save(UI / "icon_w_knife.png")
    icon_gauntlet().save(UI / "icon_w_gauntlet.png")
    icon_pipe().save(UI / "icon_w_pipe.png")
    copy_punch()
    print("saved knives, blasts, icons, punch frames")


if __name__ == "__main__":
    main()
