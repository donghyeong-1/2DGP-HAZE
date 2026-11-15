"""스테이지: 방 격자, 현재 방, 방 전환, 방 클리어(문 열림), 미니맵 데이터.

pico2d와 무관한 로직이라 창 없이 테스트할 수 있다. 방 안의 적 생성은 play_mode가 아니라 여기서 한다.
스테이지 배치 데이터는 data/stages/stage1.py (격자 좌표 -> 방 정의).
"""
import importlib.util
import os

import assets
import config
import game_world
from enemy import Enemy
from room import Room

OPPOSITE = {'L': 'R', 'R': 'L', 'U': 'D', 'D': 'U'}
STEP = {'L': (-1, 0), 'R': (1, 0), 'U': (0, 1), 'D': (0, -1)}


def load_layout(name='stage1'):
    """data/stages/<name>.py 에서 (START, 스테이지 딕셔너리)를 읽는다."""
    path = os.path.join(assets.DATA_DIR, 'stages', name + '.py')
    spec = importlib.util.spec_from_file_location('stage_data_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.START, getattr(module, name.upper())


class Stage:
    def __init__(self, player, layout=None, start=None):
        if layout is None:
            start, layout = load_layout()
        self.layout = layout
        self.player = player
        self.coord = start
        self.visited = set()
        self.cleared = set()
        self.room = None
        self.finished = False       # 탈출구(goal 방의 오른쪽 문)로 나갔는가
        self.on_clear = None        # 방을 클리어했을 때 부를 함수 (소리·글자용)

    # ----- 방 정의 -----
    def links_of(self, coord):
        """이 방에서 열 수 있는 출입구 방향: 이웃 방이 있는 쪽, 그리고 goal 방의 오른쪽(탈출구)."""
        links = set()
        for d, (dx, dy) in STEP.items():
            if (coord[0] + dx, coord[1] + dy) in self.layout:
                links.add(d)
        if self.layout[coord].get('goal'):
            links.add('R')
        return links

    # ----- 방 입장 -----
    def enter_room(self, coord, from_dir=None):
        """방을 새로 읽고 적을 세운 뒤 플레이어를 입구에 놓는다. from_dir은 들어온 쪽(왼쪽 문으로 들어오면 'L')."""
        info = self.layout[coord]
        self.coord = coord
        if self.room is not None:
            game_world.remove_object(self.room)
        for layer in (game_world.LAYER_ENEMY, game_world.LAYER_EFFECT):
            for obj in list(game_world.world[layer]):
                game_world.remove_object(obj)
        self.room = Room.load(info['template'], self.links_of(coord), info.get('high_haze', False))
        game_world.add_object(self.room, game_world.LAYER_BACKGROUND)
        p = self.player
        p.room = self.room
        if from_dir == 'L':
            p.x = config.PLAYER_HB_W / 2 + config.TILE * 1.6
        elif from_dir == 'R':
            p.x = config.SCREEN_W - config.PLAYER_HB_W / 2 - config.TILE * 1.6
        else:
            p.x = config.TILE * 3
        p.y = config.SCREEN_H - 16 * config.TILE  # 방 바닥 윗면
        p.vx = p.vy = 0.0
        p.invuln_left = max(p.invuln_left, 0.6)  # 입장 직후 잠깐 무적
        self.visited.add(coord)
        enemies = info.get('enemies', []) if coord not in self.cleared else []
        for i, (x, y) in enumerate(self.room.enemy_spawns):
            if enemies:
                kind = enemies[i % len(enemies)]
                game_world.add_object(Enemy(kind, x, y, self.room, p), game_world.LAYER_ENEMY)
        # 스폰 칸보다 적이 많으면 남는 적은 같은 칸들에 이어서 세운다
        extra = enemies[len(self.room.enemy_spawns):]
        for j, kind in enumerate(extra):
            x, y = self.room.enemy_spawns[j % len(self.room.enemy_spawns)]
            game_world.add_object(Enemy(kind, x + 40 * (j + 1), y, self.room, p), game_world.LAYER_ENEMY)
        self.room.locked = self.enemy_count() > 0

    def start(self):
        self.enter_room(self.coord)

    def enemy_count(self):
        return sum(1 for e in game_world.world[game_world.LAYER_ENEMY] if e.alive)

    # ----- 매 프레임 -----
    def update(self):
        """클리어 판정과 출입구 이동. play_mode가 world 갱신 뒤에 부른다."""
        if self.room.locked and self.enemy_count() == 0:
            self.room.locked = False
            self.cleared.add(self.coord)
            if self.on_clear:
                self.on_clear(self)
        if self.room.locked or self.player.state == 'DEAD':
            return
        p = self.player
        half = config.PLAYER_HB_W / 2
        if 'R' in self.room.links and p.x >= config.SCREEN_W - half - 2 and self._at_exit('R'):
            self._go('R')
        elif 'L' in self.room.links and p.x <= half + 2 and self._at_exit('L'):
            self._go('L')

    def _at_exit(self, direction):
        """플레이어 몸 중심 높이가 출입구 줄 중 하나에 있는가."""
        row = self.room.row_of(self.player.y + config.PLAYER_HB_H / 2)
        return any(r == row or r == row - 1 or r == row + 1 for _, r in self.room.exits.get(direction, []))

    def _go(self, direction):
        dx, dy = STEP[direction]
        target = (self.coord[0] + dx, self.coord[1] + dy)
        if target in self.layout:
            self.enter_room(target, OPPOSITE[direction])
        elif self.layout[self.coord].get('goal') and direction == 'R':
            self.finished = True

    # ----- 미니맵 -----
    def minimap_cells(self):
        """[(좌표, 상태)] 상태: 'current' / 'cleared' / 'visited' / 'unknown'. 방문한 방과 그 이웃만 보여 준다."""
        cells = []
        shown = set(self.visited)
        for c in list(self.visited):
            for dx, dy in STEP.values():
                n = (c[0] + dx, c[1] + dy)
                if n in self.layout:
                    shown.add(n)
        for c in shown:
            if c == self.coord:
                state = 'current'
            elif c in self.cleared:
                state = 'cleared'
            elif c in self.visited:
                state = 'visited'
            else:
                state = 'unknown'
            cells.append((c, state, bool(self.layout[c].get('high_haze'))))
        return cells
