"""방(Room): 텍스트 타일 맵 로드, 충돌용 타일 조회, 그리기. 방 크기는 파일마다 다르고 화면보다 커도 된다(카메라가 따라간다).

타일 문자: # 벽·바닥 / = 얇은 바닥 / ^ 가시 / P 시작 위치 / E·s·t 적 스폰(s 슬럼, t 투척병) /
           L R 좌우 출입구(벽 3칸) / U 위 출입구(맨 윗줄 3칸) / D 아래 출입구(바닥 두 줄 3칸 구멍) /
           I 아이템 진열대 / B 보스 스폰 / . 빈 칸
좌표: 원점은 방의 왼쪽 아래, y는 위로 증가. 맨 윗줄이 0줄이다 (줄 r의 아래 모서리 y = (줄 수 - r - 1) x TILE).
"""
import os

import assets
import camera
import config

SOLID = '#'
ONEWAY = '='
SPIKE = '^'
EMPTY = '.'
SPAWN_KINDS = {'s': 'slum', 't': 'thrower', 'h': 'hound', 'g': 'guard'}  # 방 텍스트의 적 스폰 표시
DOOR_CHARS = 'LRUD'
DOOR_TINT = {'gold': (255, 215, 90), 'boss': (255, 90, 100), 'shop': (120, 215, 255), 'gate': (255, 160, 70),
             'rift': (200, 130, 255), 'depart': (120, 235, 200)}   # 문 너머 방 종류 표시 색
DOOR_LABEL = {'gold': '황금방', 'boss': '보스', 'shop': '정비방', 'gate': '관문', 'rift': '균열', 'depart': '출발'}


# 타일 세트(assets/tiles/tile_set_<테마>.png)의 칸 위치 (tools/make_world.py의 build_atlas와 같다). 16열 x 9줄, 칸 60x60, 줄 0이 맨 위
#   줄 0~3  벽: 열 = 드러난 면 마스크(1 위, 2 오른쪽, 4 아래, 8 왼쪽), 줄 = 석조 무늬의 2x2 사분면
#   줄 4    벽 속(어두운 덩어리) 0~3 / 얇은 바닥 4~7 / 가시 8~9 / 벽에 붙는 소품 10~15
#   줄 5    매달리거나 바닥에 놓이는 소품   줄 6  문(좌우용 0~5, 빛 6, 위아래용 7~12, 빛 13)   줄 7~8  램프 빛(120x120)
ATLAS_H = 540
ROW_MISC, ROW_PROP, ROW_DOOR = 4, 5, 6
ATLAS_DEEP, ATLAS_ONEWAY, ATLAS_SPIKE, ATLAS_DECAL = 0, 4, 8, 10
DECAL_WINDOW, DECAL_VENT, DECAL_OUTLET, DECAL_STENCIL, DECAL_CRACK, DECAL_STAIN = range(6)
(DECOR_CHAIN_TOP, DECOR_CHAIN, DECOR_CHAIN_HOOK, DECOR_LAMP, DECOR_BANNER, DECOR_PIPE, DECOR_PIPE_VALVE, DECOR_CABLE,
 DECOR_CRATE, DECOR_BARREL, DECOR_CRYSTAL, DECOR_CRYSTAL_BIG, DECOR_DEBRIS, DECOR_VENT) = range(14)
DOOR_V, DOOR_V_BARS, DOOR_V_GLOW, DOOR_H, DOOR_H_BARS, DOOR_H_GLOW = 0, 3, 6, 7, 10, 13
GLOW_SIZE = 120                      # 램프 빛 한 장의 크기(px)
FG_PARALLAX = 1.35                    # 전경 실루엣이 카메라를 따라 움직이는 비율 (1보다 커서 플레이어보다 앞에 있는 느낌)
FAR_FADE = 1.5                        # 원경을 바꿀 때(헤이즈 심장 등장) 겹쳐 바꾸는 시간(초)
FG_THEMES = ('cell', 'foundry', 'haze')   # 전경 그림이 있는 구역 (T48)
MID_PARALLAX = (0.35, 0.12)          # 중경이 카메라를 따라 움직이는 비율 (가로, 세로)
LOCKED_TINT = (255, 130, 140)        # 전투 중 잠긴 쇠창살 문
THEMES = ('cell', 'foundry', 'haze', 'gold', 'shop', 'boss')
# 원경만 따로 있는 테마: 이름 -> 타일을 빌려 쓸 테마. 중경은 없다(원경 그림을 가리지 않게).
#   hideout(은신처, 11/19): 원경은 Codex T22, 타일은 따뜻한 녹슨 주황(foundry)이 아지트 등불과 어울린다
BACKDROP_THEMES = {'hideout': 'foundry'}


def _hash(a, b=0, c=0):
    return ((a * 73856093) ^ (b * 19349663) ^ (c * 83492791)) & 0xFFFF


class Room:
    def __init__(self, rows, links=None, high_haze=False, theme='cell', name=''):
        assert rows and all(len(r) == len(rows[0]) for r in rows), '방은 직사각형이어야 한다'
        assert len(rows) >= 12 and len(rows[0]) >= 16, f'방이 너무 작다: {len(rows[0])}x{len(rows)}'
        self.rows = rows
        self.cols, self.nrows = len(rows[0]), len(rows)
        self.width, self.height = self.cols * config.TILE, self.nrows * config.TILE
        self.is_high_haze = high_haze
        self.theme = theme if theme in THEMES or theme in BACKDROP_THEMES else 'cell'
        self.tile_theme = BACKDROP_THEMES.get(self.theme, self.theme)   # 타일·장식에 쓰는 테마
        self.has_mid = self.theme not in BACKDROP_THEMES
        self.far_over = None          # 원경을 바꿔 그릴 그림 (헤이즈 심장 결전 방, T47). far_mix 0 -> 1로 겹쳐 그린다
        self.far_mix = 0.0
        self.name = name
        self.extra_solids = {}      # (열, 줄) -> 임시 벽 조각 (보스가 세운 고철 기둥·결정 벽, boss_terrain)
        self.links = set(links or ())   # 이웃 방(또는 탈출구)이 있어서 열릴 수 있는 출입구 방향. 나머지 출입구는 벽이다
        self.locked = False             # 전투 중에는 출입구가 잠긴다
        self.door_hints = {}            # 방향 -> 문 너머 방 종류('gold', 'boss', 'shop', 'gate', 'rift'): 문 색과 이름으로 알려 준다
        self.door_texts = {}            # 방향 -> 문 이름 대신 쓸 글자 (잠긴 황금방 '남은 방 N', 균열방 '체력 -N')
        self.door_rewards = {}          # 방향 -> 문 너머 전투방을 깨면 받을 보상 ('mutation', 'shards', ..., mutations.REWARDS)
        self.spawn = (self.width / 2, config.TILE)
        self.enemy_spawns = []          # (x, y, 종류 또는 None)
        self.pedestals = []             # 진열대 칸 (x, y): 발 위치
        self.boss_spawn = None
        self.exits = {}                 # 방향 -> [(열, 줄)]
        for row, line in enumerate(rows):
            for col, ch in enumerate(line):
                x = col * config.TILE + config.TILE / 2
                y = self.height - (row + 1) * config.TILE  # 타일 아래 모서리(발 위치)
                if ch == 'P':
                    self.spawn = (x, y)
                elif ch == 'E':
                    self.enemy_spawns.append((x, y, None))          # 종류는 스테이지 데이터가 정한다
                elif ch in SPAWN_KINDS:
                    self.enemy_spawns.append((x, y, SPAWN_KINDS[ch]))  # 종류가 칸에 적혀 있다
                elif ch == 'I':
                    self.pedestals.append((x, y))
                elif ch == 'B':
                    self.boss_spawn = (x, y)
                elif ch in DOOR_CHARS:
                    self.exits.setdefault(ch, []).append((col, row))
        self._build_look()

    # ----- 겉모습 계산 (방을 읽을 때 한 번) -----
    def _wallish(self, col, row):
        """자동 타일링에서 이웃이 벽처럼 이어지는가. 방 바깥과 출입구도 벽으로 본다."""
        if col < 0 or col >= self.cols or row < 0 or row >= self.nrows:
            return True
        ch = self.rows[row][col]
        return ch == SOLID or ch in DOOR_CHARS

    def _build_look(self):
        """벽 타일의 이웃 마스크, 벽 속 칸, 벽에 붙는 소품, 장식 소품 위치를 정한다. 방 이름과 칸 좌표로만 정해지는 고정 배치다."""
        seed = sum(ord(c) for c in self.name) + self.cols
        self.masks = {}
        self.deep = set()          # 빈 칸에서 두 칸 넘게 떨어진 벽 속: 어두운 덩어리로 그린다
        self.decals = {}           # (열, 줄) -> 벽에 붙는 소품 번호 (벽 타일 위에 덧그린다)
        self.decor = []            # (소품 번호, 열, 줄)
        near_marker = set()        # 문·스폰·진열대 근처는 소품을 두지 않는다
        self.near_marker = near_marker
        for row in range(self.nrows):
            for col in range(self.cols):
                ch = self.rows[row][col]
                if ch in DOOR_CHARS or ch in 'PEstIB':
                    for dc in range(-3, 4):
                        for dr in range(-3, 4):
                            near_marker.add((col + dc, row + dr))
        for row in range(self.nrows):
            for col in range(self.cols):
                ch = self.rows[row][col]
                if not (ch == SOLID or ch in DOOR_CHARS):
                    continue
                m = 0
                if not self._wallish(col, row - 1):
                    m |= 1
                if not self._wallish(col + 1, row):
                    m |= 2
                if not self._wallish(col, row + 1):
                    m |= 4
                if not self._wallish(col - 1, row):
                    m |= 8
                self.masks[(col, row)] = m
                if m or ch != SOLID:
                    continue
                if all(self._wallish(col + dc, row + dr) for dc in range(-2, 3) for dr in range(-2, 3)):
                    self.deep.add((col, row))                    # 두 칸 안이 모두 벽이면 벽 속 (얇은 덩어리는 석조 무늬 그대로)
                inside = 0 < col < self.cols - 1 and 0 < row < self.nrows - 1
                if inside and (col, row) not in near_marker:
                    pick = _hash(col, row, seed + 3) % 100           # 벽 면의 6% 정도에 균열·얼룩·환기구·번호·배수구·창
                    if pick < 6:
                        self.decals[(col, row)] = (DECAL_CRACK, DECAL_STAIN, DECAL_VENT, DECAL_STENCIL, DECAL_OUTLET, DECAL_WINDOW)[pick]
        crystal_theme = self.theme in ('haze', 'boss', 'gold')
        for row in range(1, self.nrows - 2):
            for col in range(1, self.cols - 1):
                if (col, row) in near_marker or self.rows[row][col] != EMPTY:
                    continue
                h = _hash(col, row, seed) % 100
                above, below = self._wallish(col, row - 1), self._wallish(col, row + 1) or self.rows[row + 1][col] == ONEWAY
                if above and self.rows[row - 1][col] == SOLID:
                    if h < 7:
                        self.decor.append((DECOR_CHAIN_TOP, col, row))
                        k = 1
                        while k < 3 and row + k < self.nrows - 3 and self.rows[row + k][col] == EMPTY and _hash(col, row, k) % 3:
                            self.decor.append((DECOR_CHAIN, col, row + k))
                            k += 1
                        if k > 1:                                    # 사슬 끝은 갈고리
                            self.decor[-1] = (DECOR_CHAIN_HOOK, col, row + k - 1)
                    elif h < 11:
                        self.decor.append((DECOR_LAMP, col, row))
                    elif h < 15:
                        self.decor.append((DECOR_BANNER, col, row))
                    elif h < 19 and self.rows[row][col + 1] == EMPTY:
                        self.decor.append((DECOR_CABLE, col, row))
                    elif row == 1 and h < 55:
                        self.decor.append((DECOR_PIPE_VALVE if h % 6 == 0 else DECOR_PIPE, col, row))
                elif below and self.rows[row + 1][col] == SOLID and not above:
                    if h < 5:
                        self.decor.append((DECOR_CRATE, col, row))
                    elif h < 9:
                        self.decor.append((DECOR_BARREL, col, row))
                    elif h < (16 if self.theme == 'haze' else 11):
                        self.decor.append((DECOR_VENT, col, row))
                    elif h < (19 if self.theme == 'haze' else 14):
                        self.decor.append((DECOR_DEBRIS, col, row))
                    elif crystal_theme and h < 25:
                        self.decor.append((DECOR_CRYSTAL_BIG if h % 2 else DECOR_CRYSTAL, col, row))
        import props_anim
        self.anim_props = props_anim.place(self, self.theme)       # 움직이는 배경 소품 (Codex T28)
        self.decor_props = props_anim.place_decor(self, self.theme, self.anim_props)   # 멈춘 장식 (Codex T31)
        self.anim_time = 0.0

    @classmethod
    def load(cls, name, links=None, high_haze=False, theme='cell'):
        path = os.path.join(assets.DATA_DIR, 'rooms', name + '.txt')
        with open(path, encoding='utf-8') as f:
            rows = [line.rstrip('\r') for line in f.read().split('\n') if line.strip('\r') != '']
        return cls(rows, links, high_haze, theme, name)

    def spike_rects(self):
        """가시 타일마다 실제로 찌르는 사각형 (left, bottom, right, top). 타일 아래쪽 SPIKE_HEIGHT만 위험하다."""
        rects = []
        for row, line in enumerate(self.rows):
            for col, ch in enumerate(line):
                if ch == SPIKE:
                    bottom = self.height - (row + 1) * config.TILE
                    rects.append((col * config.TILE, bottom, (col + 1) * config.TILE, bottom + config.SPIKE_HEIGHT))
        return rects

    def line_blocked(self, x0, y0, x1, y1, step=18):
        """두 점 사이의 직선이 단단한 벽(#, 잠긴 문)에 막히는가. 근접 공격이 벽을 뚫고 맞지 않게 하는 시야 검사."""
        dist = max(abs(x1 - x0), abs(y1 - y0))
        n = max(1, int(dist // step))
        for i in range(1, n):
            t = i / n
            if self.tile_at_world(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t) == SOLID:
                return True
        return False

    def door_open(self, direction):
        return direction in self.links and not self.locked

    def door_center(self, direction):
        """출입구 칸들의 가운데 (x, 가장 아래 칸의 아래 모서리 y). 없으면 None."""
        cells = self.exits.get(direction)
        if not cells:
            return None
        cols = [c for c, _ in cells]
        rows = [r for _, r in cells]
        x = (min(cols) + max(cols) + 1) * config.TILE / 2
        y = self.height - (max(rows) + 1) * config.TILE
        return (x, y)

    # ----- 충돌용 조회 -----
    def tile_at(self, col, row):
        """격자 좌표의 타일 문자. 좌우 바깥은 벽, 위쪽 바깥은 빈 칸, 아래 바깥은 열린 아래 출입구 구멍만 빈 칸이다."""
        if row < 0:
            return EMPTY
        if col < 0 or col >= self.cols:
            return SOLID
        if row >= self.nrows:
            return EMPTY if self._hole_below(col) else SOLID
        if (col, row) in self.extra_solids:
            return SOLID
        ch = self.rows[row][col]
        if ch in DOOR_CHARS and not self.door_open(ch):
            return SOLID  # 잠겼거나 이어진 방이 없는 출입구는 벽
        return ch

    def _hole_below(self, col):
        return self.door_open('D') and any(c == col for c, _ in self.exits.get('D', []))

    @staticmethod
    def col_of(x):
        return int(x // config.TILE)

    def row_of(self, y):
        """세계 좌표 y(위로 증가)가 속한 줄 번호(맨 윗줄이 0)."""
        return int((self.height - y) // config.TILE)

    def tile_top(self, row):
        return self.height - row * config.TILE

    def tile_bottom(self, row):
        return self.height - (row + 1) * config.TILE

    def tile_at_world(self, x, y):
        return self.tile_at(self.col_of(x), self.row_of(y))

    def lights(self):
        """빛이 나는 소품의 [(x, y, 반지름, 색)] (세계 좌표). 화면 분위기(atmosphere)가 빛 번짐을 더해 그린다."""
        import atmosphere
        import props_anim
        out = []
        for p in self.anim_props + self.decor_props:
            key = p.name.split('_', 1)[1]
            if key not in atmosphere.LIGHT_COLORS:
                continue
            kind = props_anim.KIND.get(key, 'floor')
            y = p.bottom + 24 if kind == 'ceiling' else p.bottom + p.h * 0.6
            out.append((p.left + p.w / 2, y, atmosphere.LIGHT_RADIUS.get(key, 110), atmosphere.LIGHT_COLORS[key]))
        return out

    # ----- 객체 인터페이스 -----
    def update(self, dt):
        self.anim_time += dt

    def _cell(self, atlas, acol, arow, col, bottom, tint=None, flip=''):
        """타일 세트에서 한 칸을 잘라 (col, 아래 모서리 bottom)에 그린다. tint는 색 곱, flip은 'h'·'v' 뒤집기."""
        t = config.TILE
        if tint:
            from sdl2 import SDL_SetTextureColorMod
            SDL_SetTextureColorMod(atlas.texture, *tint)
        assets.draw_clip(atlas, acol * t, ATLAS_H - (arow + 1) * t, t, t, col * t, bottom, flip)
        if tint:
            SDL_SetTextureColorMod(atlas.texture, 255, 255, 255)

    def _wall(self, atlas, col, row, bottom, tint=None):
        variant = (col % 2) + 2 * (row % 2)                      # 석조 무늬의 2x2 사분면: 이웃 칸과 무늬가 이어진다
        if (col, row) in self.deep:
            self._cell(atlas, ATLAS_DEEP + variant, ROW_MISC, col, bottom, tint)
        else:
            self._cell(atlas, self.masks.get((col, row), 0), variant, col, bottom, tint)
        decal = self.decals.get((col, row))
        if decal is not None:
            self._cell(atlas, ATLAS_DECAL + decal, ROW_MISC, col, bottom, tint)

    def set_far(self, path):
        """원경을 다른 그림으로 바꾼다. step_far로 far_mix가 1이 될 때까지 원래 원경·중경 위에 겹쳐 그린다."""
        self.far_over, self.far_mix = path, 0.0

    def step_far(self, dt, seconds=FAR_FADE):
        if self.far_over is not None:
            self.far_mix = min(1.0, self.far_mix + dt / seconds)

    def _draw_backdrop(self):
        """원경(화면 고정)과 중경(카메라를 조금 따라가는 시차 배경, 가로로 이어 붙는다). 좌표는 정수만 쓴다."""
        screen_offset = assets.draw_offset
        assets.draw_offset = (0, 0)
        if self.far_over is not None and self.far_mix >= 1.0:          # 바뀐 원경만 (중경 없음)
            assets.draw_image(assets.image(self.far_over), config.SCREEN_W // 2, 0)
            assets.draw_offset = screen_offset
            return
        assets.draw_image(assets.image(f'backgrounds/far_{self.theme}.png'), config.SCREEN_W // 2, 0)
        if self.has_mid:
            self._draw_mid()
        if self.far_over is not None and self.far_mix > 0:
            assets.draw_image_tinted(assets.image(self.far_over), config.SCREEN_W // 2, 0, '', (255, 255, 255), self.far_mix)
        assets.draw_offset = screen_offset

    def _draw_mid(self):
        mid = assets.image(f'backgrounds/mid_{self.theme}.png')
        shift = int(camera.x * MID_PARALLAX[0]) % mid.w
        drop = min(mid.h - config.SCREEN_H, max(0, int(camera.y * MID_PARALLAX[1])))
        for left in (-shift, mid.w - shift):
            if left < config.SCREEN_W:
                assets.draw_clip(mid, 0, 0, mid.w, mid.h, left, -drop)

    def draw_foreground(self):
        """플레이어보다 앞에 겹치는 어두운 전경 실루엣 (T48). 화면에 붙어 가로로만 크게 밀리며 이어 붙는다.
        그림은 전투 높이(위 216~아래 60px 밖)만 채워져 있어 캐릭터·적이 가려지지 않는다."""
        if self.theme not in FG_THEMES:
            return
        fg = assets.image(f'backgrounds/fg_{self.theme}.png')
        screen_offset = assets.draw_offset
        assets.draw_offset = (0, 0)
        shift = int(camera.x * FG_PARALLAX) % fg.w
        for left in (-shift, fg.w - shift):
            if left < config.SCREEN_W:
                assets.draw_clip(fg, 0, 0, fg.w, fg.h, left, 0)
        assets.draw_offset = screen_offset

    def draw(self):
        self._draw_backdrop()
        import atmosphere
        if atmosphere.active is not None:
            atmosphere.active.draw_back()                      # 안개·빛·날씨·비네트는 배경에만: 타일·캐릭터 아래
        atlas = assets.image(f'tiles/tile_set_{self.tile_theme}.png')
        t = config.TILE
        # 화면에 보이는 칸만 그린다
        c0 = max(0, int(camera.x // t) - 1)
        c1 = min(self.cols - 1, int((camera.x + config.SCREEN_W) // t) + 1)
        r0 = max(0, self.row_of(camera.y + config.SCREEN_H) - 1)
        r1 = min(self.nrows - 1, self.row_of(camera.y) + 1)
        # 1) 램프 빛과 뒤쪽 소품
        atlas.opacify(0.55)
        for kind, col, row in self.decor:
            if kind == DECOR_LAMP and c0 - 2 <= col <= c1 + 2 and r0 - 2 <= row <= r1 + 2:
                assets.draw_clip(atlas, 0, 0, GLOW_SIZE, GLOW_SIZE, col * t + t // 2 - GLOW_SIZE // 2, self.tile_top(row) - GLOW_SIZE)
        atlas.opacify(1.0)
        for kind, col, row in self.decor:
            if c0 <= col <= c1 and r0 <= row <= r1:
                self._cell(atlas, kind, ROW_PROP, col, self.height - (row + 1) * t)
        # 1-2) 움직이는 배경 소품 (4장 반복)
        import props_anim
        view_l, view_b = camera.x - 200, camera.y - 200
        for p in self.decor_props:                                   # 멈춘 장식 먼저 (움직이는 소품보다 뒤)
            if p.left + p.w < view_l or p.left > view_l + config.SCREEN_W + 400 or p.bottom + p.h < view_b or p.bottom > view_b + config.SCREEN_H + 400:
                continue
            assets.draw_clip(assets.image(f'decor/{p.name}.png'), 0, 0, p.w, p.h, p.left, p.bottom)
        for p in self.anim_props:
            if p.left + p.w < view_l or p.left > view_l + config.SCREEN_W + 400 or p.bottom + p.h < view_b or p.bottom > view_b + config.SCREEN_H + 400:
                continue
            img = assets.image(f'props/{p.name}_{props_anim.frame_at(self.anim_time + p.phase)}.png')
            assets.draw_clip(img, 0, 0, p.w, p.h, p.left, p.bottom)
        # 2) 벽·바닥·가시·문
        for row in range(r0, r1 + 1):
            line = self.rows[row]
            bottom = self.height - (row + 1) * t
            for col in range(c0, c1 + 1):
                ch = line[col]
                if ch in DOOR_CHARS:
                    self._draw_door(ch, col, row, col * t + t // 2, bottom, atlas)
                elif ch == SOLID:
                    self._wall(atlas, col, row, bottom)
                elif ch == ONEWAY:                                   # 얇은 바닥: 0 단독, 1 왼끝, 2 가운데, 3 오른끝
                    left = col > 0 and line[col - 1] == ONEWAY
                    right = col < self.cols - 1 and line[col + 1] == ONEWAY
                    kind = 2 if left and right else 3 if left else 1 if right else 0
                    self._cell(atlas, ATLAS_ONEWAY + kind, ROW_MISC, col, bottom)
                elif ch == SPIKE:
                    self._cell(atlas, ATLAS_SPIKE + _hash(col, row) % 2, ROW_MISC, col, bottom)
        # 방이 화면보다 작으면 방 바깥을 어둡게 덮는다 (바깥으로 배경이 새어 보이지 않게)
        ink = (6, 9, 18)
        if self.width < config.SCREEN_W:
            pad = (config.SCREEN_W - self.width) // 2 + 2
            assets.draw_rect_color(-pad, -config.SCREEN_H, pad, self.height + config.SCREEN_H * 2, ink)
            assets.draw_rect_color(self.width, -config.SCREEN_H, pad, self.height + config.SCREEN_H * 2, ink)
        if self.height < config.SCREEN_H:
            pad = (config.SCREEN_H - self.height) // 2 + 2
            assets.draw_rect_color(-config.SCREEN_W, -pad, self.width + config.SCREEN_W * 2, pad, ink)
            assets.draw_rect_color(-config.SCREEN_W, self.height, self.width + config.SCREEN_W * 2, pad, ink)
        if self.is_high_haze:
            haze = assets.image('placeholder/px_cyan.png')  # 고농도 방: 화면 전체에 옅은 청록빛 안개
            haze.opacify(0.10)
            screen_offset = assets.draw_offset
            assets.draw_offset = (0, 0)
            assets.draw_rect_image(haze, 0, 0, config.SCREEN_W, config.SCREEN_H)
            assets.draw_offset = screen_offset
            haze.opacify(1.0)

    def _door_part(self, ch, col, row):
        """문 그림의 조각 번호(0 처음, 1 가운데, 2 끝). 좌우 문은 위에서 아래, 위아래 문은 왼쪽에서 오른쪽."""
        cells = self.exits.get(ch, [])
        keys = sorted({r for _, r in cells}) if ch in 'LR' else sorted({c for c, _ in cells})
        i = keys.index(row if ch in 'LR' else col)
        return 0 if i == 0 else 2 if i == len(keys) - 1 else 1

    def _draw_door(self, ch, col, row, cx, bottom, atlas):
        """출입구 그리기. 이어진 방이 없으면 벽, 잠겼으면 붉은 쇠창살, 열렸으면 문틀 안으로 문 너머 방 종류 색의 빛이 새어 들어온다."""
        if ch not in self.links:
            self._wall(atlas, col, row, bottom)
            return
        vertical = ch in 'LR'
        flip = 'h' if ch == 'R' else 'v' if ch == 'D' else ''
        if ch == 'D' and row != min(r for _, r in self.exits[ch]):
            self._cell(atlas, ATLAS_DEEP, ROW_MISC, col, bottom)     # 아래 문의 둘째 줄은 구멍 속 어둠
            return
        part = self._door_part(ch, col, row)
        if self.locked:
            self._cell(atlas, (DOOR_V_BARS if vertical else DOOR_H_BARS) + part, ROW_DOOR, col, bottom, LOCKED_TINT, flip)
            return
        self._cell(atlas, (DOOR_V if vertical else DOOR_H) + part, ROW_DOOR, col, bottom, None, flip)
        hint = self.door_hints.get(ch)
        atlas.opacify(0.85 if hint else 0.6)
        self._cell(atlas, DOOR_V_GLOW if vertical else DOOR_H_GLOW, ROW_DOOR, col, bottom, DOOR_TINT.get(hint, (120, 230, 240)), flip)
        atlas.opacify(1.0)
        cells = self.exits.get(ch, [])
        if hint in DOOR_LABEL and cells and (col, row) == cells[len(cells) // 2]:
            t = config.TILE
            label = self.door_texts.get(ch, DOOR_LABEL[hint])
            half = assets.text_width(label, True) // 2 + 40          # 긴 글자(잠긴 황금방·균열 대가)도 화면 밖으로 나가지 않게
            dx = max(70, half) if ch == 'L' else -max(70, half) if ch == 'R' else 0
            dy = 0 if ch in 'LR' else (-200 if ch == 'U' else 70)   # 위 문 글자는 화면 위쪽 HUD·안내 띠 아래로
            assets.draw_text(cx + dx, bottom + t // 2 + dy, label, DOOR_TINT[hint], small=True, center=True)
        reward = self.door_rewards.get(ch)
        if reward and cells and (col, row) == cells[len(cells) // 2]:
            self._draw_reward(ch, reward, cx, bottom)

    def _draw_reward(self, ch, reward, cx, bottom):
        """문 너머 방의 보상: 문 안쪽 옆 작은 판에 아이콘 + 이름 (하데스의 문 위 보상처럼 길을 고르게, 11/22)."""
        import hud_kit as kit
        import mutations
        name, icon, color = mutations.REWARDS[reward]
        img = assets.image(icon)
        w, h = 120, img.h + 44
        t = config.TILE
        dx = 110 if ch == 'L' else -110 if ch == 'R' else 0
        dy = 40 if ch in 'LR' else (-260 if ch == 'U' else 120)
        x, y = int(cx + dx - w // 2), int(bottom + t // 2 + dy)
        kit.panel('plate', x, y, w, h)
        assets.draw_image(img, x + w // 2, y + 32)
        kit.text(x + w // 2, y + 18, name, color, small=True, center=True)
