"""은신처 NPC: 정비사(영구 강화), 보관인(물건 하나 맡기기), 기록관(대화·기록), 무기 걸이(시작 무기, 11/23). 가까이 가서 F를 누르면 창이 열린다.

그림: assets/sprites/unified/npc_<종류>_idle_1~2.png 가 있으면 그것(Codex T22), 없으면 코드로 그린 임시 모습
(실루엣 크기·색으로 셋을 구별: 큰 몸 / 짐을 진 노인 / 책을 안은 젊은이).
"""
import os

import assets
import config
import sprites

INTERACT_RANGE = 120
NAMES = {'mechanic': '정비사', 'keeper': '보관인', 'archivist': '기록관', 'armory': '무기 걸이', 'practice': '연습장',
         'drifter': '떠돌이 죄수'}     # v8 이벤트 방 (events.py)
ROLES = {'mechanic': '기본 능력 영구 강화', 'keeper': '물건 하나 맡기기', 'archivist': '이야기·기록',
         'armory': '시작 무기 선택', 'practice': '연습장 들어가기', 'drifter': '거래'}
COLORS = {'mechanic': (240, 150, 60), 'keeper': (170, 160, 255), 'archivist': (120, 215, 255), 'armory': (230, 210, 150),
          'practice': (140, 235, 170), 'drifter': (240, 190, 120)}
# 임시 모습: (몸 폭, 키, 소품 색)
SHAPES = {'mechanic': (58, 126, (120, 128, 140)), 'keeper': (44, 117, (150, 110, 70)), 'archivist': (40, 111, (200, 180, 120)), 'armory': (192, 116, None), 'practice': (60, 120, None), 'drifter': (44, 117, (150, 110, 70))}
# 사람이 아닌 것의 그림 (Q1 2026-11-27, PixelLab, tools/apply_pixellab_props.py): 가운데 아래 기준점, 이름표는 그림 위 끝 위로
THING_ART = {'armory': 'ui/hideout_armory.png', 'practice': 'ui/hideout_practice.png'}
# 무기 걸이 그림에 걸린 무기 넷의 자리: (기준점에서 가로 px, 표시 폭 px). 왼쪽부터 철파이프(왼쪽 기둥에 기댐)·쌍권총·건틀릿·사슬
RACK_SLOTS = {'pipe': (-62, 20), 'pistol': (-30, 52), 'gauntlet': (22, 28), 'chain': (54, 24)}
RACK_MARK_Y = 16        # 표시 줄: 걸이 아래 가로대 윗면 (발에서 px)


THINGS = ('armory', 'practice')    # 사람이 아닌 것 (무기 걸이·연습장 표지판): mist에서 이름표가 인물 색 대신 밝은 회백 (R2)
PROMPT_MIST = (236, 240, 248)      # mist: 진열대 'F 획득'(S1)과 같은 밝은 회백 그림자 글자 (R1, 11/27. 경고 노랑을 쓰지 않는다)


def prompt_text(kind):
    """머리 위 안내 '<상호작용 키> 할 일'. 키는 키 설정을 따른다 (U1, 전에는 'F' 고정)."""
    import keybinds
    return f"{keybinds.label('interact', first=True)} {ROLES[kind]}"


def draw_prompt(x, y, s):
    """머리 위 상호작용 안내 ('F 기본 능력 영구 강화' 등). mist는 밝은 회백 그림자 글자(키 글자도 같은 줄에 같은 색,
    플레이 방의 진열대 안내와 같은 모양), 다른 스킨은 예전 경고 노랑 그대로."""
    import hud_kit as kit
    if kit.is_mist():
        kit.text(x, y, s, PROMPT_MIST, small=True, center=True)
    else:
        assets.draw_text(x, y, s, (255, 240, 150), small=True, center=True)


class NPC:
    def __init__(self, kind, x, y):
        self.kind, self.x, self.y = kind, x, y
        self.name = NAMES[kind]
        self.player = None
        self.time = 0.0
        self._art = os.path.exists(os.path.join(assets.ASSET_DIR, 'sprites', 'unified', f'npc_{kind}_idle_1.png'))

    def near(self, player):
        return abs(player.x - self.x) <= INTERACT_RANGE and abs(player.y - self.y) <= 160

    def update(self, dt):
        self.time += dt

    def draw(self):
        if self._art:
            frame = int(self.time / 0.6) % 2 + 1               # 숨쉬기 2장 (장당 0.6초, T22)
            face = '' if self.player is None or self.player.x >= self.x else 'h'   # 그림은 오른쪽을 본다: 플레이어 쪽을 보게
            rel = f'sprites/unified/npc_{self.kind}_idle_{frame}.png'
            r = sprites.OUTLINE_WIDTH + sprites.RIM_WIDTH                  # 테두리 판은 사방 r px 여백이 붙어 있다
            assets.draw_image(assets.outline_image(rel, sprites.OUTLINE_WIDTH, sprites.OUTLINE_COLOR, sprites.RIM_WIDTH,
                                                   sprites.RIM_COLOR), self.x, self.y - r, face)
            assets.draw_image(assets.image(rel), self.x, self.y, face)
        else:
            self._draw_placeholder()
        import game_world
        if game_world.quiet:                        # R1: mist 메뉴 창 뒤에 깔린 멈춘 은신처에서는 이름표·안내를 빼고 (그림만)
            return
        import hud_kit as kit
        color = PROMPT_MIST if self.kind in THINGS and kit.is_mist() else COLORS[self.kind]   # R2: 사람 NPC는 인물 색 그대로
        if self.kind in THING_ART:
            top = self.y + assets.image(THING_ART[self.kind]).h
        else:
            top = self.y + (132 if self._art else SHAPES[self.kind][1])
        assets.draw_text(self.x, top + 34, self.name, color, small=True, center=True)
        if self.player is not None and self.near(self.player):
            draw_prompt(self.x, top + 70, prompt_text(self.kind))

    def _draw_placeholder(self):
        if self.kind == 'armory':
            self._draw_rack()
            return
        if self.kind == 'practice':
            assets.draw_image(assets.image(THING_ART['practice']), self.x, self.y)
            return
        """그림이 오기 전 임시 모습: 외곽선 있는 몸통·머리와 하는 일을 보여 주는 소품 하나 (왼쪽을 본다)."""
        w, h, prop = SHAPES[self.kind]
        x, y = int(self.x), int(self.y)
        bob = 1 if int(self.time * 2) % 2 else 0
        body, head = (52, 58, 78), (232, 190, 150)
        assets.draw_rect_color(x - w // 2 - 2, y, w + 4, h - 26 + bob, (11, 16, 32))
        assets.draw_rect_color(x - w // 2, y + 2, w, h - 30 + bob, body)
        assets.draw_rect_color(x - 15, y + h - 30 + bob, 30, 30, (11, 16, 32))
        assets.draw_rect_color(x - 13, y + h - 28 + bob, 26, 26, head)
        if self.kind == 'mechanic':                              # 어깨에 걸친 큰 렌치
            assets.draw_rect_color(x + w // 2 - 6, y + h - 60, 10, 52, prop)
            assets.draw_rect_color(x + w // 2 - 14, y + h - 14, 26, 12, prop)
        elif self.kind == 'keeper':                              # 등에 진 상자와 등불
            assets.draw_rect_color(x + w // 2 - 4, y + 30, 30, 44, prop)
            assets.draw_rect_color(x - w // 2 - 16, y + 40, 12, 16, (255, 210, 120))
        else:                                                    # 품에 안은 장부
            assets.draw_rect_color(x - w // 2 - 6, y + 40, 26, 30, prop)
        assets.draw_rect_color(x - w // 2, y + 2, w, 6, COLORS[self.kind])   # 하는 일 색 띠

    def _draw_rack(self):
        """무기 걸이 (Q1 2026-11-27, PixelLab 그림 한 장): 네 무기가 걸려 있고, 지금 두 칸에 든 무기 아래 가로대에 불이 켜진다."""
        import meta
        x, y = int(self.x), int(self.y)
        assets.draw_image(assets.image(THING_ART['armory']), x, y)
        state = meta.state or {}
        chosen = {state.get('start_first', 'pipe'), state.get('start_weapon')}
        import hud_kit as kit
        color = PROMPT_MIST if kit.is_mist() else COLORS['armory']
        for wid, (dx, w) in RACK_SLOTS.items():
            if wid in chosen:
                assets.draw_rect_color(x + dx - w // 2, y + RACK_MARK_Y - 4, w, 4, color)
