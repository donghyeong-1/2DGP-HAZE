"""은신처 NPC: 정비사(영구 강화), 보관인(물건 하나 맡기기), 기록관(대화·기록). 가까이 가서 F를 누르면 창이 열린다.

그림: assets/sprites/unified/npc_<종류>_idle_1~2.png 가 있으면 그것(Codex T22), 없으면 코드로 그린 임시 모습
(실루엣 크기·색으로 셋을 구별: 큰 몸 / 짐을 진 노인 / 책을 안은 젊은이).
"""
import os

import assets
import config
import sprites

INTERACT_RANGE = 120
NAMES = {'mechanic': '정비사', 'keeper': '보관인', 'archivist': '기록관'}
ROLES = {'mechanic': '기본 능력 영구 강화', 'keeper': '물건 하나 맡기기', 'archivist': '이야기·기록'}
COLORS = {'mechanic': (240, 150, 60), 'keeper': (170, 160, 255), 'archivist': (120, 215, 255)}
# 임시 모습: (몸 폭, 키, 소품 색)
SHAPES = {'mechanic': (58, 126, (120, 128, 140)), 'keeper': (44, 117, (150, 110, 70)), 'archivist': (40, 111, (200, 180, 120))}


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
        color = COLORS[self.kind]
        top = self.y + (132 if self._art else SHAPES[self.kind][1])
        assets.draw_text(self.x, top + 34, self.name, color, small=True, center=True)
        if self.player is not None and self.near(self.player):
            assets.draw_text(self.x, top + 70, f'F {ROLES[self.kind]}', (255, 240, 150), small=True, center=True)

    def _draw_placeholder(self):
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
